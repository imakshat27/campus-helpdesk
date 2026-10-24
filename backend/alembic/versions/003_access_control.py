"""Session ownership and persistent request budgets."""
from alembic import op
import sqlalchemy as sa
revision='003'
down_revision='002'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('conversations',sa.Column('owner',sa.String(64),nullable=True))
    op.create_table('request_budgets',
        sa.Column('key',sa.String(160),primary_key=True),
        sa.Column('window',sa.BigInteger(),primary_key=True),
        sa.Column('count',sa.Integer(),nullable=False))

def downgrade():
    op.drop_table('request_budgets')
    op.drop_column('conversations','owner')
