"""Item names and persistent island change reports. Revision ID: 0005."""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("transactions", sa.Column("item_name", sa.String(100), nullable=True))
    op.create_table("entry_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entry_id", sa.String(32), nullable=False, unique=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_entry_reports_user_created", "entry_reports", ["user_id", "created_at"])


def downgrade():
    op.drop_index("ix_entry_reports_user_created", table_name="entry_reports")
    op.drop_table("entry_reports")
    op.drop_column("transactions", "item_name")
