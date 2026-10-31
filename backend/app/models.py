from datetime import date, datetime, timezone
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    contact: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    birth_year: Mapped[int] = mapped_column(Integer)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    demo_week_offset: Mapped[int] = mapped_column(Integer, default=0)
    tutorial_choice: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tutorial_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ParentalConsent(Base):
    __tablename__ = "parental_consents"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    accepted: Mapped[bool] = mapped_column(Boolean)
    consent_text_version: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    month: Mapped[date] = mapped_column(Date)
    amount_kopecks: Mapped[int] = mapped_column(BigInteger)
    savings_target_percent: Mapped[int] = mapped_column(Integer, default=10)
    __table_args__ = (UniqueConstraint("user_id", "month"), CheckConstraint("amount_kopecks > 0"),
                      CheckConstraint("savings_target_percent BETWEEN 0 AND 50"))


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    amount_kopecks: Mapped[int] = mapped_column(BigInteger)
    type: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str | None] = mapped_column(String(240), nullable=True)
    item_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(20), default="manual")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    entry_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (Index("ix_transactions_user_date", "user_id", "date"),
                      CheckConstraint("amount_kopecks > 0"),
                      CheckConstraint("type IN ('expense', 'saving', 'avoided_purchase')"),
                      CheckConstraint("category IN ('necessary', 'wanted', 'savings')"))


class IslandSnapshot(Base):
    __tablename__ = "island_states"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column(Date)
    prosperity: Mapped[int] = mapped_column(Integer)
    cleanliness: Mapped[int] = mapped_column(Integer)
    infrastructure: Mapped[int] = mapped_column(Integer)
    health_index: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(500))
    __table_args__ = (UniqueConstraint("user_id", "date"),)


class EntryReport(Base):
    __tablename__ = "entry_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    entry_id: Mapped[str] = mapped_column(String(32), unique=True)
    date: Mapped[date] = mapped_column(Date)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (Index("ix_entry_reports_user_created", "user_id", "created_at"),)


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    situation: Mapped[str] = mapped_column(String(500))
    options: Mapped[list] = mapped_column(JSON)


class ScenarioChoice(Base):
    __tablename__ = "scenario_choices"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    option_id: Mapped[str] = mapped_column(String(40))
    play_key: Mapped[str] = mapped_column(String(10))
    play_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effects: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("user_id", "play_key"), Index("ix_choices_user_created", "user_id", "created_at"))


class Friendship(Base):
    __tablename__ = "friendships"
    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    addressee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("requester_id", "addressee_id"),
                      Index("ix_friendships_addressee", "addressee_id", "status"),
                      CheckConstraint("requester_id <> addressee_id"),
                      CheckConstraint("status IN ('pending', 'accepted')"))
