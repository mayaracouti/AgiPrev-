from datetime import date
from decimal import Decimal

import pytest

from app.modules.evaluation.service import evaluate, metrics
from app.modules.forecasting.pipeline import Observation


def synthetic_rows():
    from app.modules.simulation.generator import financial_rows

    return [
        Observation(
            r["reference"],
            r["occurred_on"],
            r["occurred_on"],
            r["direction"],
            r["amount"],
            r["description"],
        )
        for r in financial_rows(42, 0)
    ]


def test_metrics_known_values_and_undefined_ratios():
    result = metrics([Decimal("-1"), Decimal("2")], [Decimal("-2"), Decimal("4")])
    assert result["mae"] == "1.5" and result["mse"] == "2.5"
    assert result["bias"] == "0.5" and result["f2"] == "1"
    assert result["lead_time_days"] == 1
    assert metrics([Decimal(0)], [Decimal(0)])["precision"] is None
    with pytest.raises(ValueError):
        metrics([], [])


def test_temporal_evaluation_reproducible_and_holdout_not_in_selection():
    rows = synthetic_rows()
    args = (date(2026, 7, 1), date(2026, 8, 1), date(2026, 9, 1))
    first = evaluate(rows, *args)
    assert first == evaluate(rows, *args)
    assert len(first["records"]) == 24
    assert first["model_artifact"]["trained_through"] == "2026-07-01"
    altered = [r for r in rows if r.occurred_on <= args[1]] + [
        Observation("holdout-shock", args[2], args[2], "debit", Decimal("90000"), "unexpected")
    ]
    second = evaluate(altered, *args)
    assert second["selected_model"] == first["selected_model"]
    assert [r for r in first["records"] if r["partition"] == "validation"] == [
        r for r in second["records"] if r["partition"] == "validation"
    ]
    with pytest.raises(ValueError):
        evaluate(rows, args[1], args[0], args[2])
    with pytest.raises(ValueError):
        evaluate(rows, *args, seed=10)
