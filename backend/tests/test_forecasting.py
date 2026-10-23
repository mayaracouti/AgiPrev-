from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.modules.forecasting.datasets import export_dataset
from app.modules.forecasting.engine import ExpenseModel, project
from app.modules.forecasting.pipeline import Daily, Observation, aggregate, features, temporal_split

D = Decimal
BASE = date(2026, 1, 1)


def row(ref="a", day=BASE, direction="debit", amount="10.00", **kw):
    return Observation(ref, day, kw.pop("available_on", day), direction, D(amount), **kw)


def test_auditable_series_duplicates_gaps_reversal_and_availability():
    a = row()
    reversal = row("b", BASE + timedelta(days=2), "credit", reversal_of="a")
    late = row("late", available_on=BASE + timedelta(days=10))
    series = aggregate([a, a, reversal, late], BASE, BASE + timedelta(days=2))
    assert len(series) == 3
    assert [r.expense for r in series] == [D("10"), D("0"), D("-10")]
    assert series[0].references == ("a",) and series[1].references == ()
    with pytest.raises(ValueError):
        aggregate([a, replace(a, amount=D("20"))], BASE, BASE)
    with pytest.raises(ValueError):
        aggregate([reversal], BASE, reversal.occurred_on)
    with pytest.raises(ValueError):
        aggregate([a, reversal, replace(reversal, reference="c")], BASE, reversal.occurred_on)
    with pytest.raises(ValueError):
        aggregate([row(amount="NaN")], BASE, BASE)


def test_causal_features_and_versioned_purged_splits(tmp_path):
    series = [Daily(BASE + timedelta(days=i), D(0), D(i), ()) for i in range(180)]
    target = BASE + timedelta(days=20)
    assert features(series, target) == features(series[:20], target)
    assert features(series, target)[:3] == (19.0, 13.0, 16.0)
    patterns = ({"direction": "credit", "next_date": str(target + timedelta(days=3))},)
    assert features(series, target, patterns)[-2:] == (1.0, 3.0)
    split = temporal_split(series, BASE + timedelta(days=60), BASE + timedelta(days=120))
    assert max(r.day for r in split["selection"]["train"]) + timedelta(days=30) <= BASE + timedelta(
        days=60
    )
    assert max(r.day for r in split["selection"]["validation"]) + timedelta(
        days=30
    ) <= BASE + timedelta(days=120)
    assert min(r.day for r in split["final_holdout"]) > BASE + timedelta(days=120)
    manifest = export_dataset(
        series, BASE + timedelta(days=60), BASE + timedelta(days=120), tmp_path
    )
    assert manifest["version"] == split["version"]
    assert (tmp_path / manifest["version"] / "final_holdout.json").exists()
    assert (
        temporal_split(series, BASE + timedelta(days=60), BASE + timedelta(days=120), seed=7)[
            "version"
        ]
        != split["version"]
    )
    with pytest.raises(ValueError):
        temporal_split(series[:5], BASE, BASE)


def recurring_history():
    result = [row("opening", date(2025, 11, 1), "credit", "10000")]
    for month in (1, 2, 3):
        result += [
            row(f"salary{month}", date(2026, month, 5), "credit", "1000", description="Salary"),
            row(f"rent{month}", date(2026, month, 8), "debit", "300", description="Rent"),
        ]
    for i in range(90):
        result.append(
            row(
                f"variable{i}",
                BASE + timedelta(days=i),
                amount=str(10 + i % 7),
                description=f"Shop {i % 2}",
            )
        )
    return result


@pytest.mark.parametrize("horizon", [7, 15, 30])
@pytest.mark.parametrize("method", ["constant", "moving_average", "seasonal", "hybrid"])
def test_forecasts_identity_deterministic_and_no_future(horizon, method):
    rows = recurring_history()
    cutoff = date(2026, 3, 31)
    result = project(rows, cutoff, horizon, method)
    assert (
        project(
            rows + [row("future", date(2026, 4, 1), "credit", "999999")], cutoff, horizon, method
        )
        == result
    )
    assert project(rows, cutoff, horizon, method) == result
    balance = sum((r.amount if r.direction == "credit" else -r.amount for r in rows), D(0))
    for i, point in enumerate(result["points"], 1):
        assert point["date"] == cutoff + timedelta(days=i)
        assert point["variable_expense"] >= 0
        balance += point["income"] - point["expense"]
        assert point["balance"] == balance
    if method == "hybrid":
        salary = [p for p in result["points"] if p["income"]]
        assert salary[0]["date"] == date(2026, 4, 5) and salary[0]["income"] == D("1000")
        if horizon >= 15:
            rent = next(p for p in result["points"] if p["date"] == date(2026, 4, 8))
            assert rent["fixed_expense"] == D("300") and len(rent["events"]) == 1


def test_trained_model_unseen_customer_and_month_end():
    samples = [((float(i % 7),) * 10, float(i % 7) * 2) for i in range(40)]
    model = ExpenseModel().fit(samples)
    assert model.predict((999.0,) * 10) >= 0
    assert model.version == ExpenseModel().fit(samples).version
    assert model.trees
    rows = [
        row(str(month), date(2026, month, day), "credit", "100", description="monthly")
        for month, day in ((1, 31), (2, 28), (3, 31))
    ]
    result = project(rows, date(2026, 3, 31), 30)
    assert result["points"][-1]["income"] == D("100")
    with pytest.raises(ValueError):
        project(rows, BASE, 8)


def test_laboratory_excludes_holdout_and_generates_comparison(tmp_path):
    from app.modules.forecasting.laboratory import compare, write_report

    rows = recurring_history()
    cutoff = date(2026, 3, 1)
    result = compare(rows, cutoff, 7, date(2026, 3, 20))
    assert set(result["models"]) == {"constant", "moving_average", "seasonal"}
    assert all(Decimal(r["balance_mae"]) >= 0 for r in result["models"].values())
    write_report(result, tmp_path / "laboratory.html")
    assert "Comparação de baselines" in (tmp_path / "laboratory.html").read_text()
    assert (tmp_path / "laboratory.json").exists()
    with pytest.raises(ValueError):
        compare(rows, cutoff, 30, date(2026, 3, 20))


def test_reversal_forecast_balance_and_no_reversed_recurrence():
    rows = recurring_history()
    original = next(r for r in rows if r.reference == "rent3")
    rows.append(
        row(
            "reversal",
            date(2026, 3, 31),
            "credit",
            str(original.amount),
            reversal_of=original.reference,
        )
    )
    result = project(rows, date(2026, 3, 31), 15)
    assert all(p["variable_expense"] >= 0 for p in result["points"])
    assert not any(e["description"] == "rent" for p in result["points"] for e in p["events"])


def test_dataset_exports_only_observations_available_in_each_partition(tmp_path):
    import json

    series = [Daily(BASE + timedelta(days=i), D(0), D(0), ()) for i in range(180)]
    late = row("late", BASE, available_on=BASE + timedelta(days=90))
    manifest = export_dataset(
        series, BASE + timedelta(days=60), BASE + timedelta(days=120), tmp_path, source_rows=[late]
    )
    directory = tmp_path / manifest["version"]
    train = json.loads((directory / "train.json").read_text())
    validation = json.loads((directory / "validation.json").read_text())
    assert train["observations"] == []
    assert all(D(r["expense"]) == 0 for r in train["series"])
    assert validation["observations"][0]["available_on"] == str(late.available_on)
