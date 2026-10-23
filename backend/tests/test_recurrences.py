from datetime import date, timedelta
from decimal import Decimal

from app.modules.forecasting.recurrences import detect_recurrences, evaluate
from app.modules.simulation.generator import financial_rows


def test_reproducible_profiles_and_labeled_recurrence_metrics():
    assert financial_rows(42, 0) == financial_rows(42, 0)
    assert financial_rows(42, 0) != financial_rows(43, 0)
    salaries = {
        next(r["amount"] for r in financial_rows(7, i) if r["description"] == "Salário fictício")
        for i in range(6)
    }
    assert len(salaries) == 6
    cases = []
    # Evaluation seeds differ from the UI/default seed. Labels are defined independently.
    for seed in (101, 202, 303):
        for index in range(6):
            rows = financial_rows(seed, index)
            labels = {
                ("salário fictício", "credit"),
                ("aluguel fictício", "debit"),
                ("assinatura fictícia", "debit"),
            }
            cases.append((rows, date(2026, 10, 23), labels))
    metrics = evaluate(cases)
    assert metrics["precision"] == 1.0 and metrics["recall"] >= 0.7
    assert metrics["true_positive"] + metrics["false_negative"] == 54
    print(f"RECURRENCE_METRICS: {metrics}; cases={len(cases)}")


def test_tolerances_noise_empty_history_and_future_are_excluded():
    asof = date(2026, 6, 20)
    rows = [
        {
            "occurred_on": date(2026, month, day),
            "amount": amount,
            "description": "Aluguel",
            "direction": "debit",
        }
        for month, day, amount in (
            (1, 8, "1000.00"),
            (2, 10, "1050.00"),
            (3, 6, "990.00"),
            (4, 9, "1010.00"),
        )
    ]
    assert len(detect_recurrences(rows, asof)) == 1
    assert detect_recurrences(rows[:2], asof) == []
    assert detect_recurrences([], asof) == []
    future = [{**row, "occurred_on": row["occurred_on"].replace(year=2027)} for row in rows]
    assert detect_recurrences(rows + future, asof) == detect_recurrences(rows, asof)
    irregular = [
        {**row, "occurred_on": date(2026, 1, 1) + timedelta(days=i * 4)}
        for i, row in enumerate(rows)
    ]
    assert detect_recurrences(irregular, asof) == []
    noisy = [{**row, "amount": str(Decimal("10.00") * (i + 1))} for i, row in enumerate(rows)]
    assert detect_recurrences(noisy, asof) == []
