"""Monthly recurrence heuristic. Confidence is observed regularity, not calibrated probability."""

import calendar
from collections import defaultdict
from datetime import date
from decimal import Decimal
from statistics import median


def detect_recurrences(transactions, asof: date):
    groups = defaultdict(list)
    for row in transactions:
        if row["occurred_on"] <= asof:
            groups[(row["description"].strip().casefold(), row["direction"])].append(row)
    result = []
    for (description, direction), rows in sorted(groups.items()):
        rows.sort(key=lambda row: row["occurred_on"])
        if len(rows) < 3:
            continue
        dates = [row["occurred_on"] for row in rows]
        amounts = [Decimal(row["amount"]) for row in rows]
        typical = median(amounts)
        day = int(median([value.day for value in dates]))
        gaps = [
            (right.year - left.year) * 12 + right.month - left.month
            for left, right in zip(dates, dates[1:], strict=False)
        ]
        periodicity = sum(gap == 1 for gap in gaps) / len(gaps)
        value_fit = sum(
            abs(amount - typical) <= typical * Decimal("0.10") for amount in amounts
        ) / len(amounts)
        date_fit = sum(abs(value.day - day) <= 3 for value in dates) / len(dates)
        score = min(periodicity, value_fit, date_fit)
        if score < 0.75:
            continue
        month = asof.month
        year = asof.year
        next_date = date(year, month, min(day, calendar.monthrange(year, month)[1]))
        already_posted = any(d.year == year and d.month == month for d in dates)
        if next_date <= asof or already_posted:
            year, month0 = divmod(year * 12 + month, 12)
            next_date = date(year, month0 + 1, min(day, calendar.monthrange(year, month0 + 1)[1]))
        result.append(
            {
                "description": description,
                "direction": direction,
                "amount": format(typical.quantize(Decimal("0.01")), ".2f"),
                "next_date": str(next_date),
                "period": "monthly",
                "occurrences": len(rows),
                "confidence": round(score, 4),
                "confidence_kind": "observed_regularity",
                "method": "monthly-heuristic-v2",
            }
        )
    return result


def evaluate(labeled_cases):
    tp = fp = fn = 0
    for transactions, asof, labels in labeled_cases:
        predicted = {
            (row["description"], row["direction"]) for row in detect_recurrences(transactions, asof)
        }
        tp += len(predicted & labels)
        fp += len(predicted - labels)
        fn += len(labels - predicted)
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
    }
