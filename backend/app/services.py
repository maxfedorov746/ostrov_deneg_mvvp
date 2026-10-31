import calendar
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from .island_engine import Inputs, calculate, milestones
from .models import Budget, Transaction, ScenarioChoice, IslandSnapshot, User


def month_start(day: date) -> date:
    return day.replace(day=1)


def budget_for(db: Session, user_id: int, day: date) -> Budget | None:
    return db.scalar(select(Budget).where(Budget.user_id == user_id, Budget.month == month_start(day)))


def transactions_for(db: Session, user_id: int, day: date) -> list[Transaction]:
    return list(db.scalars(select(Transaction).where(Transaction.user_id == user_id,
               Transaction.date >= month_start(day), Transaction.date <= day).order_by(Transaction.date.desc(), Transaction.id.desc())))


def streak_and_missed(transactions: list[Transaction], today: date) -> tuple[int, int]:
    days = {item.date for item in transactions if item.type != "avoided_purchase"}
    if not days:
        # A new island should never be penalized for days before its first entry.
        return 0, 0
    latest = max(days)
    missed = max(0, (today - latest).days - 1)
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak, missed


def compute_island(db: Session, user: User, today: date | None = None):
    today = today or date.today()
    budget = budget_for(db, user.id, today)
    if budget is None:
        return None
    items = transactions_for(db, user.id, today)
    necessary = sum(x.amount_kopecks for x in items if x.type == "expense" and x.category == "necessary")
    wanted = sum(x.amount_kopecks for x in items if x.type == "expense" and x.category == "wanted")
    saved = sum(x.amount_kopecks for x in items if x.type == "saving")
    avoided = sum(x.type == "avoided_purchase" for x in items)
    streak, missed = streak_and_missed(items, today)
    month_choices = list(db.scalars(select(ScenarioChoice).where(
        ScenarioChoice.user_id == user.id,
        ScenarioChoice.created_at >= month_start(today))))
    effects = tuple(max(-12, min(12, sum((choice.effects or [0, 0, 0])[i]
                                      for choice in month_choices))) for i in range(3))
    inputs = Inputs(budget.amount_kopecks, calendar.monthrange(today.year, today.month)[1],
                    today.day, necessary, wanted, saved, budget.savings_target_percent,
                    streak, avoided, missed, effects)
    state = calculate(inputs)
    return state, {"budget_kopecks": budget.amount_kopecks,
                   "remaining_kopecks": budget.amount_kopecks - necessary - wanted - saved,
                   "necessary_kopecks": necessary, "wanted_kopecks": wanted,
                   "savings_kopecks": saved, "avoided_count": avoided, "streak": streak,
                   "milestones": milestones(inputs)}


def island_dto(state, stats: dict | None = None, public: bool = False) -> dict:
    data = {"prosperity": state.prosperity, "cleanliness": state.cleanliness,
            "infrastructure": state.infrastructure, "health_index": state.health_index,
            "level": state.level, "buildings": state.buildings,
            "weather": state.weather, "pollution": state.pollution,
            "reasons": state.reasons, "savings_stage": state.savings_stage}
    if not public and stats is not None:
        data["milestones"] = stats["milestones"]
        data["stats"] = {key: value for key, value in stats.items() if key != "milestones"}
    return data


SCORE_NAMES = ("prosperity", "cleanliness", "infrastructure", "health_index")


def score_values(state) -> dict:
    return {name: getattr(state, name) for name in SCORE_NAMES}


def score_changes(previous, current) -> dict:
    return {name: getattr(current, name) - getattr(previous, name) for name in SCORE_NAMES}


def save_snapshot(db: Session, user: User) -> None:
    result = compute_island(db, user)
    if result is None:
        return
    state, _ = result
    today = date.today()
    existing = db.scalar(select(IslandSnapshot).where(IslandSnapshot.user_id == user.id,
                         IslandSnapshot.date == today))
    if existing is None:
        existing = IslandSnapshot(user_id=user.id, date=today)
        db.add(existing)
    existing.prosperity = state.prosperity
    existing.cleanliness = state.cleanliness
    existing.infrastructure = state.infrastructure
    existing.health_index = state.health_index
    existing.reason = state.reasons[0]

