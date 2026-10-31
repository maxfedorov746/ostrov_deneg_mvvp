import os
from uuid import uuid4
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import get_db
from .models import Budget, EntryReport, Friendship, IslandSnapshot, ParentalConsent, Scenario, ScenarioChoice, Transaction, User
from .schemas import AvoidedIn, BatchEntryIn, BudgetIn, ChoiceIn, FriendIn, LoginIn, RegisterIn, TransactionIn, TutorialIn
from .security import current_user, hash_password, token_for, verify_password
from .services import budget_for, compute_island, island_dto, month_start, save_snapshot, score_changes, score_values, transactions_for
from .seed import seed
from .island_engine import SAVINGS_LANDMARKS, explain
from .demo_web import attach_demo_web

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed()
    yield


app = FastAPI(title="Остров Денег API", version="0.1.0", lifespan=lifespan)


def user_dto(user: User, db: Session) -> dict:
    return {"id": user.id, "nickname": user.nickname, "birth_year": user.birth_year,
            "has_budget": budget_for(db, user.id, date.today()) is not None,
            "is_demo": user.is_demo, "tutorial_choice": user.tutorial_choice,
            "tutorial_completed": user.tutorial_completed}


def transaction_dto(item: Transaction) -> dict:
    return {"id": item.id, "amount_kopecks": item.amount_kopecks, "type": item.type,
            "category": item.category, "comment": item.comment, "item_name": item.item_name,
            "date": item.date.isoformat(),
            "is_demo": item.is_demo, "entry_id": item.entry_id}


def money(kopecks: int) -> str:
    rubles, remainder = divmod(kopecks, 100)
    return f"{rubles:,}".replace(",", " ") + (f",{remainder:02d}" if remainder else "") + " ₽"


def need_budget(db: Session, user: User) -> Budget:
    budget = budget_for(db, user.id, date.today())
    if budget is None:
        raise HTTPException(409, "Сначала задай бюджет на этот месяц")
    return budget


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    year = date.today().year
    if not year - 23 <= data.birth_year <= year - 14:
        raise HTTPException(422, "MVP рассчитан на возраст примерно 14–22 года")
    # With birth year alone, the boundary year may include a minor.
    minor_or_boundary = year - data.birth_year <= 18
    if minor_or_boundary and not data.parental_consent:
        raise HTTPException(422, "Нужно согласие родителя или законного представителя")
    user = User(nickname=data.nickname.strip(), contact=data.contact,
                password_hash=hash_password(data.password), birth_year=data.birth_year)
    db.add(user)
    try:
        db.flush()
        if minor_or_boundary:
            db.add(ParentalConsent(user_id=user.id, accepted=True, consent_text_version="mvp-1"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Никнейм или контакт уже используется")
    return {"access_token": token_for(user), "token_type": "bearer", "user": user_dto(user, db)}


@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    contact = data.contact.strip().lower()
    if "@" not in contact and contact.replace("+", "").isdigit():
        contact = "+" + contact.lstrip("+")
    user = db.scalar(select(User).where(User.contact == contact))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Неверный контакт или пароль")
    return {"access_token": token_for(user), "token_type": "bearer", "user": user_dto(user, db)}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return user_dto(user, db)


@app.put("/api/auth/tutorial")
def tutorial(data: TutorialIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if data.choice == "complete":
        if user.tutorial_choice != "guide":
            raise HTTPException(409, "Обучение ещё не начато")
        user.tutorial_completed = True
    else:
        user.tutorial_choice = data.choice
        user.tutorial_completed = data.choice == "skip"
    db.commit()
    return user_dto(user, db)


@app.get("/api/budget")
def get_budget(user: User = Depends(current_user), db: Session = Depends(get_db)):
    budget = need_budget(db, user)
    return {"amount_kopecks": budget.amount_kopecks,
            "savings_target_percent": budget.savings_target_percent, "month": budget.month.isoformat()}


@app.put("/api/budget")
def put_budget(data: BudgetIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    today = date.today()
    budget = budget_for(db, user.id, today)
    if budget is None:
        budget = Budget(user_id=user.id, month=month_start(today))
        db.add(budget)
    budget.amount_kopecks = data.amount_kopecks
    budget.savings_target_percent = data.savings_target_percent
    db.flush()
    save_snapshot(db, user)
    db.commit()
    return get_budget(user, db)


@app.get("/api/transactions")
def list_transactions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    need_budget(db, user)
    return [transaction_dto(item) for item in transactions_for(db, user.id, date.today())]


@app.post("/api/transactions", status_code=201)
def create_transaction(data: TransactionIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    need_budget(db, user)
    previous = compute_island(db, user)[0]
    if (data.type == "saving") != (data.category == "savings"):
        raise HTTPException(422, "Для сбережений выбери категорию «сбережения»")
    day = data.date or date.today()
    if day < month_start(date.today()) or day > date.today():
        raise HTTPException(422, "В MVP запись доступна за текущий месяц")
    item = Transaction(user_id=user.id, amount_kopecks=data.amount_kopecks, entry_id=uuid4().hex,
                       type=data.type, category=data.category, comment=data.comment, date=day)
    db.add(item)
    db.flush()
    save_snapshot(db, user)
    db.commit()
    island = get_island(user, db)
    return {"transaction": transaction_dto(item), "island": island,
            "explanation": explain(previous, compute_island(db, user)[0])}


@app.post("/api/transactions/avoided", status_code=201)
def avoided_purchase(data: AvoidedIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    need_budget(db, user)
    previous = compute_island(db, user)[0]
    day = data.date or date.today()
    if day < month_start(date.today()) or day > date.today():
        raise HTTPException(422, "В MVP запись доступна за текущий месяц")
    item = Transaction(user_id=user.id, amount_kopecks=data.amount_kopecks, entry_id=uuid4().hex,
                       type="avoided_purchase", category="wanted", comment=data.comment,
                       item_name=data.item_name.strip() if data.item_name else None, date=day)
    db.add(item)
    db.flush()
    save_snapshot(db, user)
    db.commit()
    island = get_island(user, db)
    return {"transaction": transaction_dto(item), "island": island,
            "explanation": explain(previous, compute_island(db, user)[0])}


@app.post("/api/transactions/batch", status_code=201)
def create_batch(data: BatchEntryIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    need_budget(db, user)
    if not (data.expense_kopecks or data.saving_kopecks or data.avoided_kopecks):
        raise HTTPException(422, "Заполни хотя бы одну сумму")
    if data.avoided_kopecks and not (data.avoided_name or "").strip():
        raise HTTPException(422, "Напиши, от какой покупки воздержался(ась)")
    if (data.avoided_name or "").strip() and not data.avoided_kopecks:
        raise HTTPException(422, "Укажи сумму покупки, от которой воздержался(ась)")
    day = data.date or date.today()
    if day < month_start(date.today()) or day > date.today():
        raise HTTPException(422, "В MVP запись доступна за текущий месяц")
    previous = compute_island(db, user)[0]
    entry_id = uuid4().hex
    items = []
    actions = []
    step_before = previous
    for amount, kind, category in (
        (data.expense_kopecks, "expense", data.expense_category),
        (data.saving_kopecks, "saving", "savings"),
        (data.avoided_kopecks, "avoided_purchase", "wanted"),
    ):
        if amount:
            item_name = data.avoided_name.strip() if kind == "avoided_purchase" and data.avoided_name else None
            item = Transaction(user_id=user.id, entry_id=entry_id, amount_kopecks=amount,
                               type=kind, category=category, comment=data.comment,
                               item_name=item_name, date=day)
            db.add(item)
            items.append(item)
            db.flush()
            step_after = compute_island(db, user)[0]
            if kind == "expense":
                label = f"Трата на {'необходимое' if category == 'necessary' else 'желаемое'}"
                note = f"Из остатка плана списано {money(amount)}."
            elif kind == "saving":
                label = "Отложено на цель"
                note = f"В сбережения добавлено {money(amount)}."
            else:
                label = f"Воздержался от покупки: {item_name}"
                note = f"{money(amount)} не списано из бюджета."
            if step_after.savings_stage > step_before.savings_stage:
                unlocked = ", ".join(SAVINGS_LANDMARKS[step_before.savings_stage:step_after.savings_stage])
                note += f" На острове открылось: {unlocked}."
            actions.append({"type": kind, "label": label, "amount_kopecks": amount,
                            "note": note, "delta": score_changes(step_before, step_after)})
            step_before = step_after
    final = step_before
    delta = score_changes(previous, final)
    summary = (explain(previous, final) if any(delta.values())
               else "Запись сохранена. Показатели пока не изменились; следующая запись приблизит цель.")
    if final.savings_stage > previous.savings_stage:
        unlocked = ", ".join(SAVINGS_LANDMARKS[previous.savings_stage:final.savings_stage])
        summary += f" Благодаря сбережениям открыто: {unlocked}."
    report = {"entry_id": entry_id, "date": day.isoformat(), "summary": summary,
              "before": score_values(previous), "after": score_values(final), "delta": delta,
              "level_before": previous.level, "level_after": final.level,
              "savings_stage_before": previous.savings_stage,
              "savings_stage_after": final.savings_stage, "actions": actions}
    db.add(EntryReport(user_id=user.id, entry_id=entry_id, date=day, payload=report))
    save_snapshot(db, user)
    db.commit()
    return {"entry_id": entry_id, "transactions": [transaction_dto(item) for item in items],
            "island": get_island(user, db),
            "explanation": summary, "report": report}


@app.get("/api/island")
def get_island(user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = compute_island(db, user)
    if result is None:
        raise HTTPException(409, "Сначала задай бюджет на этот месяц")
    return island_dto(*result)


@app.get("/api/island/history")
def island_history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    snapshots = db.scalars(select(IslandSnapshot).where(IslandSnapshot.user_id == user.id,
                   IslandSnapshot.date >= month_start(date.today())).order_by(IslandSnapshot.date))
    return [{"date": x.date.isoformat(), "health_index": x.health_index,
             "prosperity": x.prosperity, "cleanliness": x.cleanliness,
             "infrastructure": x.infrastructure, "reason": x.reason} for x in snapshots]


@app.get("/api/island/last-report")
def last_report(user: User = Depends(current_user), db: Session = Depends(get_db)):
    report = db.scalar(select(EntryReport).where(EntryReport.user_id == user.id,
                       EntryReport.date >= month_start(date.today()),
                       EntryReport.date <= date.today()).order_by(EntryReport.created_at.desc(),
                                                                  EntryReport.id.desc()))
    return report.payload if report else None


@app.get("/api/scenarios/current")
def current_scenario(user: User = Depends(current_user), db: Session = Depends(get_db)):
    need_budget(db, user)
    today = datetime.now(ZoneInfo("Europe/Moscow")).date()
    played_today = db.scalar(select(func.count(ScenarioChoice.id)).where(
        ScenarioChoice.user_id == user.id, ScenarioChoice.play_date == today)) or 0
    next_available = datetime.combine(today + timedelta(days=1), time.min,
                                      tzinfo=ZoneInfo("Europe/Moscow")).isoformat()
    if played_today >= 4:
        return {"played_today": played_today, "daily_limit": 4,
                "next_available_at": next_available, "scenario": None}
    scenarios = list(db.scalars(select(Scenario).order_by(Scenario.id)))
    if not scenarios:
        raise HTTPException(503, "Сценарии ещё загружаются")
    total = db.scalar(select(func.count(ScenarioChoice.id)).where(ScenarioChoice.user_id == user.id)) or 0
    index = total % len(scenarios)
    scenario = scenarios[index]
    return {"played_today": played_today, "daily_limit": 4,
            "next_available_at": next_available,
            "scenario": {"id": scenario.id, "title": scenario.title,
                         "situation": scenario.situation, "options": scenario.options}}


@app.post("/api/scenarios/{scenario_id}/choose")
def choose_scenario(scenario_id: str, data: ChoiceIn, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    current = current_scenario(user, db)
    today = datetime.now(ZoneInfo("Europe/Moscow")).date()
    previous = compute_island(db, user)[0]
    if current["scenario"] is None:
        raise HTTPException(429, "Сегодня пройдено четыре ситуации")
    if current["scenario"]["id"] != scenario_id:
        raise HTTPException(409, "Ситуация уже изменилась")
    option = next((x for x in current["scenario"]["options"] if x["id"] == data.option_id), None)
    if option is None:
        raise HTTPException(422, "Такого варианта нет")
    slot = current["played_today"] + 1
    db.add(ScenarioChoice(user_id=user.id, scenario_id=scenario_id, option_id=data.option_id,
                          play_key=f"{today:%Y%m%d}{slot}", play_date=today,
                          effects=option["effects"]))
    try:
        db.flush()
        save_snapshot(db, user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Эта ситуация уже пройдена")
    return {"consequence": option["consequence"], "island": get_island(user, db),
            "explanation": explain(previous, compute_island(db, user)[0])}


def friendship_for(db: Session, first: int, second: int):
    return db.scalar(select(Friendship).where(or_(
        (Friendship.requester_id == first) & (Friendship.addressee_id == second),
        (Friendship.requester_id == second) & (Friendship.addressee_id == first))))


@app.get("/api/friends")
def friends(user: User = Depends(current_user), db: Session = Depends(get_db)):
    relationships = db.scalars(select(Friendship).where(or_(Friendship.requester_id == user.id,
                                                              Friendship.addressee_id == user.id)))
    result = []
    for rel in relationships:
        other = db.get(User, rel.addressee_id if rel.requester_id == user.id else rel.requester_id)
        result.append({"id": other.id, "nickname": other.nickname, "status": rel.status,
                       "incoming": rel.addressee_id == user.id, "friendship_id": rel.id})
    return result


@app.post("/api/friends/requests", status_code=201)
def request_friend(data: FriendIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    other = db.scalar(select(User).where(User.nickname == data.nickname.strip()))
    if other is None or other.id == user.id:
        raise HTTPException(404, "Друг с таким никнеймом не найден")
    rel = friendship_for(db, user.id, other.id)
    if rel is not None:
        raise HTTPException(409, "Запрос уже существует")
    rel = Friendship(requester_id=user.id, addressee_id=other.id, status="pending")
    db.add(rel)
    db.commit()
    return {"id": rel.id, "status": rel.status}


@app.post("/api/friends/requests/{friendship_id}/accept")
def accept_friend(friendship_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rel = db.get(Friendship, friendship_id)
    if rel is None or rel.addressee_id != user.id or rel.status != "pending":
        raise HTTPException(404, "Запрос не найден")
    rel.status = "accepted"
    db.commit()
    return {"status": "accepted"}


@app.get("/api/friends/{friend_id}/island")
def friend_island(friend_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rel = friendship_for(db, user.id, friend_id)
    if rel is None or rel.status != "accepted":
        raise HTTPException(403, "Остров виден только друзьям")
    other = db.get(User, friend_id)
    result = compute_island(db, other)
    if result is None:
        raise HTTPException(404, "У друга пока нет острова")
    state, _ = result
    public = island_dto(state, public=True)
    # A public island intentionally excludes reasons: they may hint at spending patterns.
    public.pop("reasons")
    return {"nickname": other.nickname, "island": public}


@app.post("/api/demo/fill")
def demo_fill(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not DEMO_MODE:
        raise HTTPException(404, "Демо-режим выключен")
    budget = budget_for(db, user.id, date.today())
    if budget is None:
        budget = Budget(user_id=user.id, month=month_start(date.today()),
                        amount_kopecks=600_000, savings_target_percent=10)
        db.add(budget)
    existing = db.scalar(select(Transaction.id).where(Transaction.user_id == user.id,
                         Transaction.is_demo == True, Transaction.date >= month_start(date.today())))
    if existing is None:
        today = date.today()
        samples = [(3, 120_000, "expense", "necessary", "Продукты"),
                   (2, 65_000, "expense", "wanted", "Кино"),
                   (1, 40_000, "expense", "necessary", "Проезд"),
                   (0, 60_000, "saving", "savings", "На цель")]
        for days_back, amount, kind, category, comment in samples:
            day = max(month_start(today), today - timedelta(days=days_back))
            db.add(Transaction(user_id=user.id, amount_kopecks=amount, type=kind,
                               category=category, comment=comment, date=day, is_demo=True))
    demo_friend = db.scalar(select(User).where(User.nickname == "ОстровДруг"))
    if demo_friend and friendship_for(db, user.id, demo_friend.id) is None:
        db.add(Friendship(requester_id=user.id, addressee_id=demo_friend.id, status="accepted"))
    db.flush()
    save_snapshot(db, user)
    db.commit()
    return {"island": get_island(user, db), "message": "Демо-данные добавлены"}


# The production Compose stack serves this frontend through nginx instead.
if os.getenv("FRONTEND_DIST"):
    attach_demo_web(app, os.environ["FRONTEND_DIST"])

