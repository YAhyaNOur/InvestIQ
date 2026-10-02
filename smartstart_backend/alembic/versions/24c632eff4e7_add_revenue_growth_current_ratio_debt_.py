from alembic import op
import sqlalchemy as sa

revision = '24c632eff4e7'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('companies', sa.Column('revenue_growth', sa.Float(), nullable=True))
    op.add_column('companies', sa.Column('current_ratio',  sa.Float(), nullable=True))
    op.add_column('companies', sa.Column('debt_to_equity', sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column('companies', 'debt_to_equity')
    op.drop_column('companies', 'current_ratio')
    op.drop_column('companies', 'revenue_growth')