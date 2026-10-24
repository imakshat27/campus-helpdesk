"""Public source provenance, campus and retrieval timestamp."""
from alembic import op
import sqlalchemy as sa
revision='002'
down_revision='001'
branch_labels=None
depends_on=None
def upgrade():
 for name,kind in [('source_url',sa.Text()),('campus',sa.String(40)),('retrieved_at',sa.String(40))]:
  op.add_column('documents',sa.Column(name,kind,nullable=True))
def downgrade():
 for name in ['retrieved_at','campus','source_url']:op.drop_column('documents',name)
