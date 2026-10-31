import pytest
from app.island_engine import Inputs, calculate, explain, milestones


BASE = Inputs(budget=600_000, days_in_month=30, elapsed_days=10)


def test_initial_island_has_valid_indicators():
    island = calculate(BASE)
    assert island.health_index == 50
    assert island.level == 2
    assert island.buildings == ("Причал", "Домики")


def test_saving_and_streak_help_island():
    improved = calculate(Inputs(**{**BASE.__dict__, "saved": 60_000, "streak": 7}))
    initial = calculate(BASE)
    assert improved.prosperity > initial.prosperity
    assert improved.infrastructure > initial.infrastructure
    assert "выросла" in explain(initial, improved)


def test_financial_center_can_be_unlocked_without_scenarios():
    grown = calculate(Inputs(**{**BASE.__dict__, "saved": 60_000, "streak": 7,
                                "avoided_count": 5}))
    assert grown.level == 5
    assert "Финансовый центр" in grown.buildings


def test_voluntary_saving_helps_with_zero_target():
    no_target = calculate(Inputs(**{**BASE.__dict__, "savings_target_percent": 0}))
    saved = calculate(Inputs(**{**BASE.__dict__, "savings_target_percent": 0, "saved": 10_000}))
    assert saved.prosperity > no_target.prosperity


def test_wants_above_threshold_reduce_cleanliness():
    low = calculate(Inputs(**{**BASE.__dict__, "necessary": 70_000, "wanted": 30_000}))
    high = calculate(Inputs(**{**BASE.__dict__, "necessary": 30_000, "wanted": 70_000}))
    assert high.cleanliness < low.cleanliness


def test_avoided_purchase_does_not_reduce_budget_and_helps_cleanliness():
    initial = calculate(BASE)
    avoided = calculate(Inputs(**{**BASE.__dict__, "avoided_count": 1}))
    assert avoided.cleanliness > initial.cleanliness


def test_overspend_and_missed_days_are_bounded_and_reversible():
    stressed = calculate(Inputs(**{**BASE.__dict__, "wanted": 900_000, "missed_days": 20}))
    recovered = calculate(BASE)
    assert all(0 <= value <= 100 for value in (stressed.prosperity, stressed.cleanliness,
                                                stressed.infrastructure, stressed.health_index))
    assert recovered.health_index > stressed.health_index


def test_invalid_inputs_fail():
    with pytest.raises(ValueError):
        calculate(Inputs(budget=0, days_in_month=30, elapsed_days=10))


def test_savings_landmarks_advance_one_goal_at_a_time():
    start = milestones(BASE)
    assert start["next_name"] == "Сад"
    assert start["next_target_kopecks"] == 30_000
    garden = milestones(Inputs(**{**BASE.__dict__, "saved": 30_000}))
    assert garden["savings_stage"] == 1
    assert garden["next_name"] == "Теплица"
    assert milestones(Inputs(**{**BASE.__dict__, "saved": 90_000}))["savings_progress_percent"] == 50
    assert calculate(Inputs(**{**BASE.__dict__, "saved": 30_000})).savings_stage == 1


def test_risk_meter_uses_only_allocated_money():
    data = Inputs(**{**BASE.__dict__, "necessary": 200_000, "saved": 100_000,
                     "avoided_count": 3})
    progress = milestones(data)
    assert progress["risk_remaining_kopecks"] == 300_000
    assert progress["risk_progress_percent"] == 50


def test_landmark_and_overspend_boundaries_are_exact_kopecks():
    almost_garden = milestones(Inputs(**{**BASE.__dict__, "saved": 29_999}))
    assert almost_garden["savings_stage"] == 0
    assert almost_garden["to_next_kopecks"] == 1
    garden = milestones(Inputs(**{**BASE.__dict__, "saved": 30_000}))
    assert garden["savings_stage"] == 1
    assert garden["next_name"] == "Теплица"
    full = milestones(Inputs(**{**BASE.__dict__, "necessary": 600_000}))
    assert full["risk_remaining_kopecks"] == 0
    assert full["risk_over_kopecks"] == 0
    assert milestones(Inputs(**{**BASE.__dict__, "necessary": 600_001}))["risk_over_kopecks"] == 1
