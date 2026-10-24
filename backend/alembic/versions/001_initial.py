"""Initial approved knowledge, conversations and staff tickets."""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
revision='001'
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.create_table('documents',sa.Column('id',sa.String(80),primary_key=True),sa.Column('title',sa.String(200),nullable=False),sa.Column('category',sa.String(40),nullable=False),sa.Column('kind',sa.String(20),nullable=False),sa.Column('content',sa.Text(),nullable=False),sa.Column('approved',sa.Boolean(),nullable=False))
    op.create_index('ix_documents_category','documents',['category'])
    op.create_table('chunks',sa.Column('id',sa.String(100),primary_key=True),sa.Column('document_id',sa.String(80),sa.ForeignKey('documents.id',ondelete='CASCADE'),nullable=False),sa.Column('heading',sa.String(200),nullable=False),sa.Column('content',sa.Text(),nullable=False),sa.Column('embedding',Vector(384),nullable=False))
    op.create_index('ix_chunks_document_id','chunks',['document_id'])
    op.create_table('conversations',sa.Column('id',sa.String(36),primary_key=True),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_table('messages',sa.Column('id',sa.String(36),primary_key=True),sa.Column('conversation_id',sa.String(36),sa.ForeignKey('conversations.id'),nullable=False),sa.Column('role',sa.String(20),nullable=False),sa.Column('content',sa.Text(),nullable=False),sa.Column('outcome',sa.String(30)),sa.Column('sources',sa.JSON(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_messages_conversation_id','messages',['conversation_id'])
    op.create_table('tickets',sa.Column('id',sa.String(36),primary_key=True),sa.Column('reference',sa.String(24),unique=True,nullable=False),sa.Column('conversation_id',sa.String(36),sa.ForeignKey('conversations.id'),nullable=False),sa.Column('query',sa.Text(),nullable=False),sa.Column('reason',sa.String(100),nullable=False),sa.Column('status',sa.String(20),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_tickets_conversation_id','tickets',['conversation_id'])
    op.create_index('ix_tickets_status','tickets',['status'])

def downgrade():
    for name in ['tickets','messages','conversations','chunks','documents']:
        op.drop_table(name)
