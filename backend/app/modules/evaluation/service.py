"""Causal validation selection followed by a single isolated final evaluation."""

import hashlib
import json
from dataclasses import asdict
from datetime import date, timedelta
from decimal import Decimal

from app.modules.forecasting.engine import project, train_expense_model
from app.modules.forecasting.pipeline import Observation, aggregate, eligible

METHODS = ("constant", "moving_average", "seasonal", "hybrid")


def metrics(actual: list[Decimal], predicted: list[Decimal]) -> dict:
    if not actual or len(actual) != len(predicted):
        raise ValueError("Aligned nonempty actual/predicted series required")
    errors = [p - a for a, p in zip(actual, predicted, strict=True)]
    n = Decimal(len(errors))
    mse = sum((e * e for e in errors), Decimal(0)) / n
    tp = sum(a < 0 and p < 0 for a, p in zip(actual, predicted, strict=True))
    fp = sum(a >= 0 and p < 0 for a, p in zip(actual, predicted, strict=True))
    fn = sum(a < 0 and p >= 0 for a, p in zip(actual, predicted, strict=True))

    def ratio(a, b):
        return str(Decimal(a) / Decimal(b)) if b else None

    first_actual = next((i for i, a in enumerate(actual) if a < 0), None)
    first_predicted = next((i for i, p in enumerate(predicted) if p < 0), None)
    return {
        "mae": str(sum(map(abs, errors)) / n),
        "mse": str(mse),
        "rmse": str(mse.sqrt()),
        "bias": str(sum(errors) / n),
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "f1": ratio(2 * tp, 2 * tp + fp + fn),
        "f2": ratio(5 * tp, 5 * tp + fp + 4 * fn),
        "lead_time_days": first_actual + 1
        if first_actual is not None
        and first_predicted is not None
        and first_predicted <= first_actual
        else None,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "samples": len(actual),
    }


def dataset_digest(rows: list[Observation], final_end: date) -> str:
    return hashlib.sha256(
        json.dumps(
            [asdict(r) for r in sorted(eligible(rows, final_end), key=lambda r: r.reference)],
            default=str,
            sort_keys=True,
        ).encode()
    ).hexdigest()


def evaluate(
    rows: list[Observation], train_end: date, validation_end: date, final_end: date, seed: int = 42
) -> dict:
    if seed != 42:
        raise ValueError("This deterministic engine supports seed 42 only")
    if not train_end < validation_end < final_end:
        raise ValueError("Strict chronological partitions required")
    if (validation_end - train_end).days < 30 or (final_end - validation_end).days < 30:
        raise ValueError("Validation and isolated holdout each require 30 realized days")
    known = eligible(rows, final_end)
    if not known or min(r.occurred_on for r in known) >= train_end:
        raise ValueError("Realized data must cover training and final evaluation")
    dataset = dataset_digest(rows, final_end)
    daily = aggregate(known, min(r.occurred_on for r in known), final_end)
    balances, balance = {}, Decimal(0)
    for d in daily:
        balance += d.income - d.expense
        balances[d.day] = balance
    # Model fitted only on training; never refitted on validation or holdout.
    trained = train_expense_model(rows, train_end)
    if trained is None:
        raise ValueError("Insufficient training history for frozen hybrid model")
    artifact = {
        "base": trained.base,
        "trees": trained.trees,
        "version": trained.version,
        "trained_through": str(train_end),
    }
    records = []

    def partition(origin, partition_name, methods):
        for horizon in (7, 15, 30):
            for method in methods:
                forecast = project(rows, origin, horizon, method, expense_model=trained)
                actual = [balances[origin + timedelta(days=i)] for i in range(1, horizon + 1)]
                predicted = [p["balance"] for p in forecast["points"]]
                records.append(
                    {
                        "partition": partition_name,
                        "model": method,
                        "horizon": horizon,
                        "model_version": forecast["model_version"],
                        "metrics": metrics(actual, predicted),
                        "series": [
                            {
                                "date": str(p["date"]),
                                "observed": str(a),
                                "predicted": str(p["balance"]),
                            }
                            for p, a in zip(forecast["points"], actual, strict=True)
                        ],
                    }
                )

    partition(train_end, "validation", METHODS)
    selected = min(
        METHODS,
        key=lambda method: (
            sum(Decimal(r["metrics"]["mae"]) for r in records if r["model"] == method),
            method,
        ),
    )
    # Selection is frozen before any final-holdout prediction or metric is calculated.
    partition(validation_end, "final_holdout", METHODS)
    return {
        "experiment_version": "evaluation-v1",
        "dataset_version": dataset,
        "seed": seed,
        "train_end": str(train_end),
        "validation_end": str(validation_end),
        "final_end": str(final_end),
        "selected_model": selected,
        "model_artifact": artifact,
        "hyperparameters": {"trees": 12, "learning_rate": "0.2", "lags": [1, 7], "seed": seed},
        "records": records,
        "limitations": [
            "Dados exclusivamente sintéticos; sem garantia de generalização bancária.",
            "Incerteza não calibrada; métricas indefinidas são null.",
            "Lead time: dias da origem ao primeiro déficit realizado, se sinalizado antes.",
            "Seleção pela soma do MAE de validação nos horizontes 7/15/30; holdout excluído.",
        ],
    }
