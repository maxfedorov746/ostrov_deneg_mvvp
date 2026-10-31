import json
from datetime import date
from importlib.resources import files
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_db
from app.main import app
from app.models import Scenario


def client_with_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions() as db:
        for item in json.loads(files("app").joinpath("scenarios.json").read_text(encoding="utf-8")):
            db.add(Scenario(**item))
        db.commit()

    def override():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = override
    return TestClient(app), engine


def register(client, nickname, contact):
    response = client.post("/api/auth/register", json={"nickname": nickname, "contact": contact,
        "password": "a-strong-password", "birth_year": date.today().year - 17,
        "parental_consent": True})
    assert response.status_code == 201, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_registration_budget_transaction_avoided_and_scenario():
    client, engine = client_with_db()
    try:
        denied = client.post("/api/auth/register", json={"nickname": "MinorOne", "contact": "minor@example.ru",
            "password": "a-strong-password", "birth_year": date.today().year - 17,
            "parental_consent": False})
        assert denied.status_code == 422
        auth = register(client, "MinorOne", "minor@example.ru")
        assert client.get("/api/auth/me", headers=auth).json()["tutorial_choice"] is None
        started = client.put("/api/auth/tutorial", headers=auth, json={"choice": "guide"})
        assert started.json()["tutorial_completed"] is False
        finished = client.put("/api/auth/tutorial", headers=auth, json={"choice": "complete"})
        assert finished.json()["tutorial_completed"] is True
        budget = client.put("/api/budget", headers=auth, json={"amount_kopecks": 600000,
            "savings_target_percent": 10})
        assert budget.status_code == 200
        before = client.get("/api/island", headers=auth).json()
        assert before["health_index"] == 50
        expense = client.post("/api/transactions", headers=auth, json={"amount_kopecks": 35000,
            "type": "expense", "category": "necessary"})
        assert expense.status_code == 201, expense.text
        after_expense = expense.json()["island"]
        assert after_expense["stats"]["remaining_kopecks"] == 565000
        avoided = client.post("/api/transactions/avoided", headers=auth,
            json={"amount_kopecks": 10000})
        assert avoided.status_code == 201, avoided.text
        assert avoided.json()["island"]["stats"]["remaining_kopecks"] == 565000
        assert avoided.json()["island"]["cleanliness"] > after_expense["cleanliness"]
        for played in range(4):
            current = client.get("/api/scenarios/current", headers=auth).json()
            assert current["played_today"] == played
            scenario = current["scenario"]
            chosen = client.post(f"/api/scenarios/{scenario['id']}/choose", headers=auth,
                json={"option_id": scenario["options"][0]["id"]})
            assert chosen.status_code == 200, chosen.text
        capped = client.get("/api/scenarios/current", headers=auth).json()
        assert capped["played_today"] == 4
        assert capped["scenario"] is None
        assert capped["next_available_at"]
        assert client.post(f"/api/scenarios/{scenario['id']}/choose", headers=auth,
            json={"option_id": scenario["options"][0]["id"]}).status_code == 429
        assert before["stats"]["remaining_kopecks"] == 600000
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_batch_entry_is_atomic_and_shared_in_history():
    client, engine = client_with_db()
    try:
        auth = register(client, "BatchUser", "batch@example.ru")
        client.put("/api/budget", headers=auth, json={"amount_kopecks": 600000})
        assert client.post("/api/transactions/batch", headers=auth, json={}).status_code == 422
        assert client.post("/api/transactions/batch", headers=auth,
            json={"avoided_kopecks": 10000}).status_code == 422
        assert client.post("/api/transactions/batch", headers=auth,
            json={"expense_kopecks": 10000, "avoided_name": "Наушники"}).status_code == 422
        saved = client.post("/api/transactions/batch", headers=auth, json={
            "expense_kopecks": 35000, "expense_category": "necessary", "saving_kopecks": 20000,
            "avoided_kopecks": 10000, "avoided_name": "Наушники", "comment": "Один день"})
        assert saved.status_code == 201, saved.text
        body = saved.json()
        assert len(body["transactions"]) == 3
        assert {item["entry_id"] for item in body["transactions"]} == {body["entry_id"]}
        assert body["island"]["stats"]["remaining_kopecks"] == 545000
        assert body["transactions"][-1]["item_name"] == "Наушники"
        report = body["report"]
        assert len(report["actions"]) == 3
        assert "Наушники" in report["actions"][-1]["label"]
        assert client.get("/api/island/last-report", headers=auth).json() == report
        assert {key: sum(action["delta"][key] for action in report["actions"])
                for key in report["delta"]} == report["delta"]
        history = client.get("/api/transactions", headers=auth).json()
        assert len(history) == 3
        assert {item["comment"] for item in history} == {"Один день"}
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_tutorial_can_be_skipped_and_stays_completed():
    client, engine = client_with_db()
    try:
        auth = register(client, "SkipUser", "skip@example.ru")
        skipped = client.put("/api/auth/tutorial", headers=auth, json={"choice": "skip"})
        assert skipped.status_code == 200
        assert skipped.json()["tutorial_choice"] == "skip"
        assert client.get("/api/auth/me", headers=auth).json()["tutorial_completed"] is True
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_friend_public_island_excludes_financial_data():
    client, engine = client_with_db()
    try:
        first = register(client, "FirstUser", "first@example.ru")
        second = register(client, "SecondUser", "second@example.ru")
        client.put("/api/budget", headers=first, json={"amount_kopecks": 600000})
        client.put("/api/budget", headers=second, json={"amount_kopecks": 400000})
        denied = client.get("/api/friends/2/island", headers=first)
        assert denied.status_code == 403
        request = client.post("/api/friends/requests", headers=first, json={"nickname": "SecondUser"})
        assert request.status_code == 201
        accepted = client.post(f"/api/friends/requests/{request.json()['id']}/accept", headers=second)
        assert accepted.status_code == 200
        friend_id = client.get("/api/friends", headers=first).json()[0]["id"]
        public = client.get(f"/api/friends/{friend_id}/island", headers=first)
        assert public.status_code == 200, public.text
        raw = public.text
        assert all(secret not in raw for secret in ("amount_kopecks", "remaining_kopecks", "stats",
                                                 "contact", "birth_year", "reasons", "transactions"))
        assert public.json()["island"]["health_index"] >= 0
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
