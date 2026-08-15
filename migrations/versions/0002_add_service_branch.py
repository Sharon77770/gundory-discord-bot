"""store the selected military service branch

Revision ID: 0002_add_service_branch
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_add_service_branch"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("military_profiles")}
    if "service_branch" not in columns:
        op.add_column("military_profiles", sa.Column("service_branch", sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column("military_profiles", "service_branch")
