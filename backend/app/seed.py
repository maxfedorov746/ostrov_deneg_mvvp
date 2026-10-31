import json
import os
from datetime import date, timedelta
from importlib.resources import files
from sqlalchemy import select
from .db import SessionLocal
from .models import Budget, Friendship, Scenario, Transaction, User
from .security import hash_password


def seed() -> None:
    scenarios = json.loads(files("app").joinpath("scenarios.json").read_text(encoding="utf-8"))
    with SessionLocal() as db:
        for entry in scenarios:
            scenario = db.get(Scenario, entry["id"])
            if scenario is None:
                db.add(Scenario(**entry))
            else:
                scenario.title = entry["title"]
                scenario.situation = entry["situation"]
                scenario.options = entry["options"]
        friend = db.scalar(select(User).where(User.nickname == "ОстровДруг")) if os.getenv("DEMO_MODE", "false").lower() == "true" else None
        if os.getenv("DEMO_MODE", "false").lower() == "true" and friend is None:
            friend = User(nickname="ОстровДруг", contact="demo-friend@local.test",
                          password_hash=hash_password("DemoFriend2026!"), birth_year=2000, is_demo=True)
            db.add(friend)
            db.flush()
        if friend is not None:
            today = date.today()
            from .services import budget_for
            if budget_for(db, friend.id, today) is None:
                db.add(Budget(user_id=friend.id, month=today.replace(day=1), amount_kopecks=500_000,
                              savings_target_percent=10))
                db.add_all([
                    Transaction(user_id=friend.id, amount_kopecks=100_000, type="expense", category="necessary",
                                date=max(today.replace(day=1), today - timedelta(days=1)), is_demo=True),
                    Transaction(user_id=friend.id, amount_kopecks=50_000, type="saving", category="savings",
                                date=today, is_demo=True),
                ])
        db.commit()
