"""Deterministic baselines and trained gradient boosted regression stumps."""

import calendar
import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal
from statistics import mean, median

from app.modules.forecasting.pipeline import Daily, Observation, aggregate, eligible, features
from app.modules.forecasting.recurrences import detect_recurrences

CENT = Decimal("0.01")


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT)


class ExpenseModel:
    """Squared-error boosting, fixed order/ties; no customer identifier as a feature."""

    def __init__(self):
        self.base = 0.0
        self.trees: list[tuple[int, float, float, float]] = []
        self.version = ""

    def fit(self, samples: list[tuple[tuple[float, ...], float]]) -> "ExpenseModel":
        if not samples:
            raise ValueError("Training history required")
        self.base = mean(y for _, y in samples)
        self.trees = []
        prediction = [self.base] * len(samples)
        for _ in range(12):
            residual = [y - p for (_, y), p in zip(samples, prediction, strict=True)]
            best = None
            for column in range(len(samples[0][0])):
                values = sorted({x[column] for x, _ in samples})
                thresholds = values[:: max(1, len(values) // 8)]
                for threshold in thresholds:
                    left = [
                        r
                        for (x, _), r in zip(samples, residual, strict=True)
                        if x[column] <= threshold
                    ]
                    right = [
                        r
                        for (x, _), r in zip(samples, residual, strict=True)
                        if x[column] > threshold
                    ]
                    if not left or not right:
                        continue
                    a, b = mean(left), mean(right)
                    loss = sum((r - a) ** 2 for r in left) + sum((r - b) ** 2 for r in right)
                    candidate = (loss, column, threshold, a * 0.2, b * 0.2)
                    if best is None or candidate < best:
                        best = candidate
            if best is None:
                break
            _, column, threshold, a, b = best
            self.trees.append((column, threshold, a, b))
            prediction = [
                p + (a if x[column] <= threshold else b)
                for (x, _), p in zip(samples, prediction, strict=True)
            ]
        digest = hashlib.sha256(json.dumps(samples).encode()).hexdigest()[:16]
        self.version = "boosted-stumps-v1:" + digest
        return self

    def predict(self, x: tuple[float, ...]) -> Decimal:
        return money(max(0.0, self.base + sum(a if x[c] <= t else b for c, t, a, b in self.trees)))


def variable_observations(rows: list[Observation], recurring_keys: set) -> list[Observation]:
    references = {
        r.reference
        for r in rows
        if r.direction == "debit"
        and not r.reversal_of
        and (r.description.strip().casefold(), r.direction) not in recurring_keys
    }
    return [r for r in rows if r.reference in references or r.reversal_of in references]


def project(rows: list[Observation], cutoff: date, horizon: int, method: str = "hybrid") -> dict:
    if horizon not in (7, 15, 30) or method not in (
        "hybrid",
        "constant",
        "moving_average",
        "seasonal",
    ):
        raise ValueError("Invalid forecast configuration")
    known = eligible(rows, cutoff)
    start = min((r.occurred_on for r in known), default=cutoff)
    daily = aggregate(known, start, cutoff)
    balance = sum((r.income - r.expense for r in daily), Decimal("0.00"))
    recurring_rows = [
        r
        for r in known
        if not r.reversal_of and r.reference not in {s.reversal_of for s in known if s.reversal_of}
    ]
    recurrences = detect_recurrences(
        [
            {
                "description": r.description,
                "direction": r.direction,
                "amount": r.amount,
                "occurred_on": r.occurred_on,
            }
            for r in recurring_rows
        ],
        cutoff,
    )
    recurring_keys = {(r["description"], r["direction"]) for r in recurrences}
    variable_rows = variable_observations(known, recurring_keys)
    variable = aggregate(variable_rows, start, cutoff)
    samples = []
    for i, day_row in enumerate(daily):
        if i < 7:
            continue
        origin = day_row.day - timedelta(days=1)
        past = eligible(known, origin)
        reversed_past = {r.reversal_of for r in past if r.reversal_of}
        past_rows = [r for r in past if not r.reversal_of and r.reference not in reversed_past]
        patterns = detect_recurrences(
            [
                {
                    "description": r.description,
                    "direction": r.direction,
                    "amount": r.amount,
                    "occurred_on": r.occurred_on,
                }
                for r in past_rows
            ],
            origin,
        )
        keys = {(r["description"], r["direction"]) for r in patterns}
        historical_variable = variable_observations(past, keys)
        causal = aggregate(historical_variable, start, origin)
        target_series = aggregate(variable_observations(known, keys), day_row.day, day_row.day)
        target = max(Decimal(0), target_series[0].expense)
        samples.append((features(causal, day_row.day, tuple(patterns)), float(target)))
    model = ExpenseModel().fit(samples) if samples else None
    version = (
        model.version
        if method == "hybrid" and model
        else ("hybrid-insufficient-history-v1" if method == "hybrid" else method + "-v1")
    )
    points = []
    for offset in range(1, horizon + 1):
        day = cutoff + timedelta(days=offset)
        income = expense = fixed = Decimal("0.00")
        events = []
        if method == "hybrid":
            for recurrence in recurrences:
                next_date = date.fromisoformat(recurrence["next_date"])
                nominal_day = int(
                    median(
                        r.occurred_on.day
                        for r in recurring_rows
                        if r.description.strip().casefold() == recurrence["description"]
                        and r.direction == recurrence["direction"]
                    )
                )
                due = date(
                    day.year,
                    day.month,
                    min(nominal_day, calendar.monthrange(day.year, day.month)[1]),
                )
                if day == due and day >= next_date:
                    amount = Decimal(recurrence["amount"])
                    events.append({**recurrence, "date": str(day), "uncertainty": "uncalibrated"})
                    if recurrence["direction"] == "credit":
                        income += amount
                    else:
                        fixed += amount
            expense = (
                model.predict(features(variable, day, tuple(recurrences)))
                if model
                else Decimal("0.00")
            )
            variable.append(Daily(day, Decimal(0), expense, ()))
        elif method == "moving_average":
            recent = daily[-7:]
            income = money(sum(r.income for r in recent) / len(recent))
            expense = money(max(Decimal(0), sum(r.expense for r in recent) / len(recent)))
        elif method == "seasonal":
            source = next(
                (r for r in daily if r.day == cutoff - timedelta(days=(7 - offset % 7) % 7)),
                daily[-1],
            )
            income, expense = source.income, max(Decimal(0), source.expense)
        balance += income - fixed - expense
        points.append(
            {
                "date": day,
                "income": income,
                "fixed_expense": fixed,
                "variable_expense": expense,
                "expense": fixed + expense,
                "balance": balance,
                "events": events,
            }
        )
    dataset = hashlib.sha256(repr(known).encode()).hexdigest()
    return {
        "base_date": cutoff,
        "horizon": horizon,
        "method": method,
        "model_version": version,
        "dataset_version": dataset,
        "seed": 42,
        "points": points,
        "risk": next(
            ({"date": p["date"], "balance": p["balance"]} for p in points if p["balance"] < 0), None
        ),
        "estimate_notice": "Estimativa demonstrativa com dados fictícios; incerteza não calibrada.",
    }
