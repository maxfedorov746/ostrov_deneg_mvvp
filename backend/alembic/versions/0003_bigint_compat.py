"""Upgrade amounts from early demo databases when necessary. Revision ID: 0003."""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    for table in ("budgets", "transactions"):
        column = next(c for c in sa.inspect(bind).get_columns(table) if c["name"] == "amount_kopecks")
        if not isinstance(column["type"], sa.BigInteger):
            with op.batch_alter_table(table) as batch:
                batch.alter_column("amount_kopecks", type_=sa.BigInteger(),
                                   existing_type=column["type"], existing_nullable=False)


def downgrade():
    # The initial published schema already uses BIGINT; keep monetary precision.
    pass
