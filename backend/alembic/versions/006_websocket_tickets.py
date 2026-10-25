"""Short-lived, single-use authentication for direct WebSocket connections."""
from alembic import op
import sqlalchemy as sa
revision='006'
down_revision='005'
branch_labels=depends_on=None

def upgrade():
    op.create_table('websocket_tickets',sa.Column('token_hash',sa.String(64),primary_key=True),
                    sa.Column('session_hash',sa.String(64),sa.ForeignKey('login_sessions.token_hash',ondelete='CASCADE'),nullable=False),
                    sa.Column('expires_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_websocket_tickets_session_hash','websocket_tickets',['session_hash'])

def downgrade():
    op.drop_table('websocket_tickets')
