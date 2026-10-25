"""Conversation state, durable message order and idempotent submissions."""
from alembic import op
import sqlalchemy as sa
revision='005'
down_revision='004'
branch_labels=depends_on=None

def upgrade():
    op.add_column('conversations',sa.Column('state',sa.String(30),nullable=False,server_default='ai'))
    op.add_column('conversations',sa.Column('updated_at',sa.DateTime(timezone=True),nullable=True))
    op.add_column('conversations',sa.Column('next_sequence',sa.Integer(),nullable=False,server_default='1'))
    op.create_index('ix_conversations_owner','conversations',['owner'])
    with op.batch_alter_table('messages') as batch:
        batch.add_column(sa.Column('sequence',sa.Integer(),nullable=True))
        batch.add_column(sa.Column('sender_id',sa.String(36),nullable=True))
        batch.add_column(sa.Column('details',sa.JSON(),nullable=False,server_default='{}'))
        batch.create_foreign_key('fk_message_sender','users',['sender_id'],['id'])
        batch.create_unique_constraint('uq_message_sequence',['conversation_id','sequence'])
    with op.batch_alter_table('tickets') as batch:
        batch.add_column(sa.Column('message_id',sa.String(36),nullable=True))
        batch.create_foreign_key('fk_ticket_message','messages',['message_id'],['id'])
    connection=op.get_bind()
    # Portable, deterministic backfill; never claim legacy ownership.
    connection.execute(sa.text("""
        WITH numbered AS (
          SELECT id, ROW_NUMBER() OVER (PARTITION BY conversation_id ORDER BY created_at, id) AS seq
          FROM messages
        )
        UPDATE messages SET sequence=(SELECT seq FROM numbered WHERE numbered.id=messages.id)
    """))
    # Retain duplicate historical tickets as resolved; only the newest stays open.
    connection.execute(sa.text("""
        WITH ranked AS (
          SELECT id, ROW_NUMBER() OVER (PARTITION BY conversation_id ORDER BY created_at DESC,id DESC) AS position
          FROM tickets WHERE status='open'
        )
        UPDATE tickets SET status='resolved' WHERE id IN (SELECT id FROM ranked WHERE position>1)
    """))
    connection.execute(sa.text("""
        UPDATE conversations SET updated_at=created_at,
          next_sequence=COALESCE((SELECT MAX(sequence)+1 FROM messages WHERE conversation_id=conversations.id),1),
          state=CASE
            WHEN EXISTS (SELECT 1 FROM tickets WHERE conversation_id=conversations.id AND status='open') THEN 'waiting_for_staff'
            WHEN EXISTS (SELECT 1 FROM tickets WHERE conversation_id=conversations.id) THEN 'resolved'
            ELSE 'ai' END
    """))
    with op.batch_alter_table('conversations') as batch:
        batch.alter_column('updated_at',existing_type=sa.DateTime(timezone=True),nullable=False)
    op.create_index('uq_open_ticket_conversation','tickets',['conversation_id'],unique=True,postgresql_where=sa.text("status = 'open'"),sqlite_where=sa.text("status = 'open'"))
    op.create_table('submissions',sa.Column('id',sa.String(36),primary_key=True),
                    sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),
                    sa.Column('request_id',sa.String(36),nullable=False),
                    sa.Column('conversation_id',sa.String(36),sa.ForeignKey('conversations.id'),nullable=False),
                    sa.Column('content',sa.Text(),nullable=False),sa.Column('result',sa.JSON(),nullable=False),
                    sa.UniqueConstraint('user_id','request_id',name='uq_submission_request'))

def downgrade():
    op.drop_table('submissions')
    op.drop_index('uq_open_ticket_conversation',table_name='tickets')
    with op.batch_alter_table('tickets') as batch:
        batch.drop_constraint('fk_ticket_message',type_='foreignkey')
        batch.drop_column('message_id')
    with op.batch_alter_table('messages') as batch:
        batch.drop_constraint('uq_message_sequence',type_='unique')
        batch.drop_constraint('fk_message_sender',type_='foreignkey')
        for column in ['sequence','sender_id','details']:batch.drop_column(column)
    op.drop_index('ix_conversations_owner',table_name='conversations')
    for column in ['state','updated_at','next_sequence']:op.drop_column('conversations',column)
