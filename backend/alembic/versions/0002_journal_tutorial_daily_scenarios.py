"""Journal groups, first-run guide, and daily scenario play. Revision ID: 0002."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("tutorial_choice", sa.String(10), nullable=True))
    op.add_column("users", sa.Column("tutorial_completed", sa.Boolean(), nullable=False,
                                     server_default=sa.false()))
    op.add_column("transactions", sa.Column("entry_id", sa.String(32), nullable=True))
    op.create_index("ix_transactions_entry_id", "transactions", ["entry_id"])
    op.add_column("scenario_choices", sa.Column("play_date", sa.Date(), nullable=True))


def downgrade():
    op.drop_column("scenario_choices", "play_date")
    op.drop_index("ix_transactions_entry_id", table_name="transactions")
    op.drop_column("transactions", "entry_id")
    op.drop_column("users", "tutorial_completed")
    op.drop_column("users", "tutorial_choice")
