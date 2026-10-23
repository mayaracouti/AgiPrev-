"""TASK-041: new explicit CT-001..018 mapping; fictitious deterministic fixtures."""

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.modules.forecasting.engine import ExpenseModel, project
from app.modules.forecasting.pipeline import Observation, aggregate, features

D = Decimal
CUT = date(2026, 3, 31)


def entry(ref, day=CUT, direction="credit", amount="1000", description=""):
    return Observation(ref, day, day, direction, D(amount), description)


@pytest.fixture
def monthly():
    return [
        entry(f"{name}{month}", date(2026, month, day), direction, amount, name)
        for month in (1, 2, 3)
        for name, day, direction, amount in (
            ("salary", 5, "credit", "1000"),
            ("rent", 8, "debit", "300"),
        )
    ]


def test_CT_001_positive_balance():
    assert project([entry("opening")], CUT, 7, "constant")["risk"] is None


def test_CT_002_deficit():
    result = project([entry("expense", direction="debit")], CUT, 7, "constant")
    assert result["risk"] == {"date": CUT + timedelta(days=1), "balance": D("-1000")}


def test_CT_003_zero_is_not_deficit():
    assert project([], CUT, 7)["risk"] is None


def test_CT_004_salary_date_value(monthly):
    points = project(monthly, CUT, 7)["points"]
    assert [(p["date"], p["income"]) for p in points if p["income"]] == [
        (date(2026, 4, 5), D(1000))
    ]


def test_CT_005_rent_no_double_count(monthly):
    points = project(monthly, CUT, 15)["points"]
    assert sum(p["fixed_expense"] for p in points) == D(300)
    assert sum(p["variable_expense"] for p in points) == 0


def test_CT_006_short_month():
    rows = [
        entry(str(m), date(2026, m, d), description="salary")
        for m, d in ((1, 31), (2, 28), (3, 31))
    ]
    assert project(rows, CUT, 30)["points"][-1]["income"] == D(1000)


def test_CT_007_future_excluded(monthly):
    assert project(monthly, CUT, 7) == project(
        monthly + [entry("future", date(2026, 4, 1))], CUT, 7
    )


def test_CT_008_late_availability(monthly):
    late = replace(entry("late"), available_on=CUT + timedelta(days=1))
    assert project(monthly, CUT, 7) == project(monthly + [late], CUT, 7)


def test_CT_009_duplicate_idempotent():
    item = entry("same")
    assert project([item], CUT, 7) == project([item, item], CUT, 7)


def test_CT_010_conflicting_duplicate():
    with pytest.raises(ValueError, match="Conflicting"):
        project([entry("same"), entry("same", amount="2")], CUT, 7)


def test_CT_011_reversal_restores_balance():
    original = entry("debit", direction="debit", amount="100")
    reversal = replace(entry("reverse", amount="100"), reversal_of="debit")
    assert project([original, reversal], CUT, 7, "constant")["points"][0]["balance"] == 0


def test_CT_012_orphan_reversal_rejected():
    with pytest.raises(ValueError, match="reversal"):
        project([replace(entry("reverse"), reversal_of="missing")], CUT, 7)


def test_CT_013_gaps_zero():
    series = aggregate([entry("one")], CUT, CUT + timedelta(days=2))
    assert [p.income for p in series] == [D(1000), D(0), D(0)]


def test_CT_014_invalid_money_rejected():
    for invalid in ("NaN", "Infinity", "0", "-1"):
        with pytest.raises(ValueError):
            project([entry("invalid", amount=invalid)], CUT, 7)


def test_CT_015_features_causal():
    history = aggregate([entry("one", direction="debit")], CUT, CUT + timedelta(days=2))
    assert features(history, CUT + timedelta(days=1)) == features(
        history[:1], CUT + timedelta(days=1)
    )


def test_CT_016_unseen_features_nonnegative():
    model = ExpenseModel().fit([((float(i),) * 10, float(i % 3)) for i in range(10)])
    assert model.predict((999.0,) * 10) >= 0
    assert (
        model.version
        == ExpenseModel().fit([((float(i),) * 10, float(i % 3)) for i in range(10)]).version
    )


def test_CT_017_all_horizons_identity(monthly):
    for horizon in (7, 15, 30):
        result = project(monthly, CUT, horizon)
        balance = D(2100)
        assert len(result["points"]) == horizon
        for point in result["points"]:
            balance += point["income"] - point["expense"]
            assert point["balance"] == balance


def test_CT_018_baselines_deterministic_invalid_horizon(monthly):
    for method in ("constant", "moving_average", "seasonal"):
        assert project(monthly, CUT, 7, method) == project(monthly, CUT, 7, method)
    with pytest.raises(ValueError):
        project(monthly, CUT, 8)
