"""Fixed role accounts and revocable login sessions."""
from alembic import op
import sqlalchemy as sa
revision = '004'
down_revision = '003'
branch_labels = depends_on = None

def upgrade():
    op.create_table('users', sa.Column('id', sa.String(36), primary_key=True),
                    sa.Column('username', sa.String(100), nullable=False, unique=True),
                    sa.Column('role', sa.String(20), nullable=False, unique=True),
                    sa.Column('password_hash', sa.Text(), nullable=False))
    op.create_table('login_sessions', sa.Column('token_hash', sa.String(64), primary_key=True),
                    sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
                    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_login_sessions_user_id', 'login_sessions', ['user_id'])

def downgrade():
    op.drop_table('login_sessions')
    op.drop_table('users')
