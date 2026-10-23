"""Auditable daily data and strictly causal feature preparation. Money remains Decimal."""

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from statistics import mean, pstdev

ZERO = Decimal("0.00")


@dataclass(frozen=True)
class Observation:
    reference: str
    occurred_on: date
    available_on: date
    direction: str
    amount: Decimal
    description: str = ""
    reversal_of: str | None = None


@dataclass(frozen=True)
class Daily:
    day: date
    income: Decimal
    expense: Decimal
    references: tuple[str, ...]


def eligible(rows: Iterable[Observation], cutoff: date) -> list[Observation]:
    unique: dict[str, Observation] = {}
    for row in rows:
        if row.occurred_on > cutoff or row.available_on > cutoff:
            continue
        if (
            not row.amount.is_finite()
            or row.amount <= 0
            or row.direction not in ("credit", "debit")
        ):
            raise ValueError("Invalid ledger observation")
        if row.reference in unique and unique[row.reference] != row:
            raise ValueError("Conflicting duplicate reference")
        unique[row.reference] = row
    reversals: set[str] = set()
    for row in unique.values():
        if row.reversal_of:
            original = unique.get(row.reversal_of)
            if (
                original is None
                or original.reversal_of
                or original.amount != row.amount
                or original.direction == row.direction
                or original.occurred_on > row.occurred_on
                or original.reference in reversals
            ):
                raise ValueError("Invalid or duplicate reversal")
            reversals.add(original.reference)
    return sorted(unique.values(), key=lambda r: (r.occurred_on, r.reference))


def aggregate(rows: Iterable[Observation], start: date, cutoff: date) -> list[Daily]:
    if start > cutoff:
        raise ValueError("Start must precede cutoff")
    grouped: dict[date, list[Observation]] = {}
    for row in eligible(rows, cutoff):
        grouped.setdefault(row.occurred_on, []).append(row)
    result = []
    for offset in range((cutoff - start).days + 1):
        day = start + timedelta(days=offset)
        entries = grouped.get(day, [])
        # Reversals stay on their posting day and reverse the original flow category.
        income = sum(
            (
                r.amount * (-1 if r.reversal_of else 1)
                for r in entries
                if (r.direction == "credit") != bool(r.reversal_of)
            ),
            ZERO,
        )
        expense = sum(
            (
                r.amount * (-1 if r.reversal_of else 1)
                for r in entries
                if (r.direction == "debit") != bool(r.reversal_of)
            ),
            ZERO,
        )
        result.append(Daily(day, income, expense, tuple(r.reference for r in entries)))
    return result


def features(series: list[Daily], target: date, recurrences: tuple = ()) -> tuple[float, ...]:
    history = sorted((r for r in series if r.day < target), key=lambda r: r.day)
    by_day = {r.day: float(r.expense) for r in history}
    window = [by_day.get(target - timedelta(days=i), 0.0) for i in range(1, 8)]
    next_income = [
        date.fromisoformat(r["next_date"])
        for r in recurrences
        if r["direction"] == "credit" and date.fromisoformat(r["next_date"]) >= target
    ]
    days_to_income = min(((d - target).days for d in next_income), default=-1)
    return (
        by_day.get(target - timedelta(days=1), 0.0),
        by_day.get(target - timedelta(days=7), 0.0),
        mean(window),
        pstdev(window),
        float(target.weekday()),
        float(target.day),
        float(target.month),
        float(target.weekday() >= 5),
        float(len(recurrences)),
        float(days_to_income),
    )


def temporal_split(
    series: list[Daily], train_end: date, validation_end: date, horizon: int = 30, seed: int = 42
) -> dict:
    ordered = sorted(series, key=lambda r: r.day)
    if len({r.day for r in ordered}) != len(ordered) or horizon < 1:
        raise ValueError("Unique dates and positive horizon required")
    # Purge origins whose labels could cross into the next partition.
    train = [r for r in ordered if r.day + timedelta(days=horizon) <= train_end]
    validation = [
        r
        for r in ordered
        if train_end < r.day and r.day + timedelta(days=horizon) <= validation_end
    ]
    holdout = [r for r in ordered if r.day > validation_end]
    if not train or not validation or not holdout or train_end >= validation_end:
        raise ValueError("Insufficient temporal partitions")
    payload = [(str(r.day), str(r.income), str(r.expense), r.references) for r in ordered]
    version = hashlib.sha256(
        json.dumps(
            [payload, seed, horizon, str(train_end), str(validation_end)], sort_keys=True
        ).encode()
    ).hexdigest()
    return {
        "version": version,
        "seed": seed,
        "horizon": horizon,
        "selection": {"train": train, "validation": validation},
        "final_holdout": holdout,
    }
