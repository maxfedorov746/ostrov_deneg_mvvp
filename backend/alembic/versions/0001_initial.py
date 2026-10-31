"""Initial PostgreSQL schema. Revision ID: 0001."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nickname", sa.String(32), nullable=False),
        sa.Column("contact", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("birth_year", sa.Integer(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("demo_week_offset", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_nickname", "users", ["nickname"], unique=True)
    op.create_index("ix_users_contact", "users", ["contact"], unique=True)
    op.create_table("parental_consents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("consent_text_version", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("amount_kopecks", sa.BigInteger(), nullable=False),
        sa.Column("savings_target_percent", sa.Integer(), nullable=False),
        sa.UniqueConstraint("user_id", "month"),
        sa.CheckConstraint("amount_kopecks > 0"),
        sa.CheckConstraint("savings_target_percent BETWEEN 0 AND 50"))
    op.create_table("transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_kopecks", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("comment", sa.String(240), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_kopecks > 0"),
        sa.CheckConstraint("type IN ('expense', 'saving', 'avoided_purchase')"),
        sa.CheckConstraint("category IN ('necessary', 'wanted', 'savings')"))
    op.create_index("ix_transactions_user_date", "transactions", ["user_id", "date"])
    op.create_table("island_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("prosperity", sa.Integer(), nullable=False),
        sa.Column("cleanliness", sa.Integer(), nullable=False),
        sa.Column("infrastructure", sa.Integer(), nullable=False),
        sa.Column("health_index", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.UniqueConstraint("user_id", "date"))
    op.create_table("scenarios",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("situation", sa.String(500), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False))
    op.create_table("scenario_choices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_id", sa.String(40), sa.ForeignKey("scenarios.id"), nullable=False),
        sa.Column("option_id", sa.String(40), nullable=False),
        sa.Column("week_key", sa.String(10), nullable=False),
        sa.Column("effects", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "week_key"))
    op.create_index("ix_choices_user_created", "scenario_choices", ["user_id", "created_at"])
    op.create_table("friendships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("requester_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("addressee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("requester_id", "addressee_id"),
        sa.CheckConstraint("requester_id <> addressee_id"),
        sa.CheckConstraint("status IN ('pending', 'accepted')"))
    op.create_index("ix_friendships_addressee", "friendships", ["addressee_id", "status"])


def downgrade():
    op.drop_index("ix_friendships_addressee", table_name="friendships")
    op.drop_table("friendships")
    op.drop_index("ix_choices_user_created", table_name="scenario_choices")
    op.drop_table("scenario_choices")
    op.drop_table("scenarios")
    op.drop_table("island_states")
    op.drop_index("ix_transactions_user_date", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("budgets")
    op.drop_table("parental_consents")
    op.drop_index("ix_users_contact", table_name="users")
    op.drop_index("ix_users_nickname", table_name="users")
    op.drop_table("users")
