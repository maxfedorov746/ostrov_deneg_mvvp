"""Name the scenario choice slot by its actual meaning. Revision ID: 0004."""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("scenario_choices", "week_key", new_column_name="play_key")


def downgrade():
    op.alter_column("scenario_choices", "play_key", new_column_name="week_key")
