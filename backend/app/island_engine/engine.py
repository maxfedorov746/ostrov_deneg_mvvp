"""Deterministic island rules. No database or web framework dependencies."""

from dataclasses import dataclass, field


def clamp(value: float) -> int:
    return round(max(0, min(100, value)))


@dataclass(frozen=True)
class Inputs:
    budget: int  # kopecks
    days_in_month: int
    elapsed_days: int
    necessary: int = 0
    wanted: int = 0
    saved: int = 0
    savings_target_percent: int = 10
    streak: int = 0
    avoided_count: int = 0
    missed_days: int = 0
    scenario_effects: tuple[int, int, int] = (0, 0, 0)


@dataclass(frozen=True)
class IslandState:
    prosperity: int
    cleanliness: int
    infrastructure: int
    health_index: int
    level: int
    buildings: tuple[str, ...]
    weather: str
    pollution: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    savings_stage: int = 0


BUILDINGS = ("Причал", "Домики", "Мастерская", "Парк", "Финансовый центр")
SAVINGS_LANDMARKS = ("Сад", "Теплица", "Маяк")
SAVINGS_THRESHOLDS = (5, 15, 30)


def milestones(data: Inputs) -> dict:
    """Exact kopeck thresholds for visible saving landmarks and overspending risk."""
    if data.budget <= 0 or min(data.necessary, data.wanted, data.saved) < 0:
        raise ValueError("Budget must be positive and amounts non-negative")
    targets = [(data.budget * percent + 99) // 100 for percent in SAVINGS_THRESHOLDS]
    stage = sum(data.saved >= target for target in targets)
    next_target = targets[stage] if stage < len(targets) else None
    progress = min(100, round(100 * data.saved / next_target)) if next_target else 100
    allocated = data.necessary + data.wanted + data.saved
    return {
        "savings_stage": stage,
        "next_name": SAVINGS_LANDMARKS[stage] if next_target else None,
        "next_target_kopecks": next_target,
        "to_next_kopecks": max(0, next_target - data.saved) if next_target else 0,
        "savings_progress_percent": progress,
        "allocated_kopecks": allocated,
        "risk_remaining_kopecks": max(0, data.budget - allocated),
        "risk_over_kopecks": max(0, allocated - data.budget),
        "risk_progress_percent": min(100, round(100 * allocated / data.budget)),
    }


def calculate(data: Inputs) -> IslandState:
    if data.budget <= 0 or data.days_in_month < 28 or data.days_in_month > 31:
        raise ValueError("Budget must be positive and days_in_month must be 28–31")
    if not 1 <= data.elapsed_days <= data.days_in_month:
        raise ValueError("elapsed_days must fit the month")
    if not 0 <= data.savings_target_percent <= 50:
        raise ValueError("savings_target_percent must be 0–50")
    if min(data.necessary, data.wanted, data.saved, data.streak,
           data.avoided_count, data.missed_days) < 0:
        raise ValueError("Input totals and counts cannot be negative")

    regularity = min(data.streak, 7) / 7
    # A zero target removes the obligation, but voluntary saving still helps.
    target = data.budget * (data.savings_target_percent or 10) / 100
    savings = min(1.0, data.saved / target) if target else 0.0
    spending = data.necessary + data.wanted
    wants_share = data.wanted / spending if spending else 0.0
    wants_excess = max(0.0, wants_share - 0.35) / 0.65
    restraint = min(data.avoided_count, 5) / 5
    missed = min(data.missed_days, 7) / 7
    overspend = min(1.0, max(0.0, (spending + data.saved - data.budget) / data.budget))
    sp, sc, si = data.scenario_effects

    prosperity = clamp(50 + 24 * savings + 8 * regularity - 20 * overspend - 8 * missed + sp)
    cleanliness = clamp(55 + 6 * regularity + 12 * restraint - 22 * wants_excess - 16 * overspend - 8 * missed + sc)
    infrastructure = clamp(45 + 25 * regularity + 6 * savings - 18 * overspend - 10 * missed + si)
    health = clamp(0.4 * prosperity + 0.3 * cleanliness + 0.3 * infrastructure)
    level = 1 + sum(health >= threshold for threshold in (40, 55, 70, 78))
    weather = "солнечно" if health >= 70 else "переменная облачность" if health >= 45 else "дождь"
    pollution = "чисто" if cleanliness >= 65 else "немного мусора" if cleanliness >= 40 else "нужна уборка"
    reasons = []
    if data.streak:
        reasons.append(f"Ты записывал(а) траты {data.streak} дн. подряд — инфраструктура растёт.")
    if data.saved:
        reasons.append("Пополнение сбережений помогает острову процветать.")
    if data.avoided_count:
        reasons.append("Воздержание от импульсивной покупки сделало остров чище; деньги остались в бюджете.")
    if wants_excess:
        reasons.append("Доля желаемого выше 35% трат. Запиши следующую покупку осознанно — чистота восстановится.")
    if overspend:
        reasons.append("План на месяц превышен. Новый бюджет и спокойные записи помогут восстановить остров.")
    if data.missed_days:
        reasons.append("После паузы остров немного притих. Одна новая запись вернёт движение.")
    if any(data.scenario_effects):
        reasons.append("Выбор в ситуации повлиял на остров. Это тренировка без списания денег.")
    if not reasons:
        reasons.append("Остров готов расти. Начни с первой записи.")
    return IslandState(prosperity, cleanliness, infrastructure, health, level,
                       BUILDINGS[:level], weather, pollution, tuple(reasons), milestones(data)["savings_stage"])


def explain(previous: IslandState, current: IslandState) -> str:
    changes = {
        "процветание": current.prosperity - previous.prosperity,
        "чистота": current.cleanliness - previous.cleanliness,
        "инфраструктура": current.infrastructure - previous.infrastructure,
    }
    name, delta = max(changes.items(), key=lambda item: abs(item[1]))
    if delta == 0:
        return current.reasons[0]
    direction = "выросла" if delta > 0 else "снизилась"
    reason_terms = {
        ("процветание", True): ("Пополнение", "записывал", "Выбор"),
        ("процветание", False): ("План на месяц", "После паузы", "Выбор"),
        ("чистота", True): ("Воздержание", "записывал", "Выбор"),
        ("чистота", False): ("Доля желаемого", "План на месяц", "После паузы", "Выбор"),
        ("инфраструктура", True): ("записывал", "Пополнение", "Выбор"),
        ("инфраструктура", False): ("План на месяц", "После паузы", "Выбор"),
    }
    reason = next((r for term in reason_terms[(name, delta > 0)] for r in current.reasons if term in r), current.reasons[0])
    return f"{name.capitalize()} {direction} на {abs(delta)}. {reason}"
