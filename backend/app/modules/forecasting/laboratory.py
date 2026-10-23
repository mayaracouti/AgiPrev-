"""Technical laboratory: executed baseline comparison, outside banking navigation."""

import argparse
import html
import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.modules.forecasting.engine import project
from app.modules.forecasting.pipeline import Observation, aggregate
from app.modules.forecasting.router import observations


def compare(rows: list[Observation], cutoff: date, horizon: int, validation_end: date) -> dict:
    end = cutoff + timedelta(days=horizon)
    if end > validation_end:
        raise ValueError("Selection cannot access final holdout")
    if not rows or max(r.occurred_on for r in rows) < end:
        raise ValueError("Complete realized evaluation horizon required")
    actual = aggregate(rows, min(r.occurred_on for r in rows), end)
    balance = Decimal(0)
    balances = {}
    for row in actual:
        balance += row.income - row.expense
        balances[row.day] = balance
    result = {}
    for method in ("constant", "moving_average", "seasonal"):
        forecast = project(rows, cutoff, horizon, method)
        errors = [abs(p["balance"] - balances[p["date"]]) for p in forecast["points"]]
        result[method] = {
            "balance_mae": str(sum(errors) / len(errors)),
            "points": forecast["points"],
        }
    return {
        "cutoff": str(cutoff),
        "horizon": horizon,
        "validation_end": str(validation_end),
        "models": result,
        "purpose": "validation selection only; final holdout excluded",
    }


def write_report(result: dict, destination: Path):
    rows = "".join(
        "<tr><td>"
        + html.escape(method)
        + "</td><td>"
        + html.escape(data["balance_mae"])
        + "</td></tr>"
        for method, data in result["models"].items()
    )
    daily = "".join(
        "<tr><td>"
        + html.escape(str(p["date"]))
        + "</td><td>"
        + method
        + "</td><td>"
        + html.escape(str(p["balance"]))
        + "</td></tr>"
        for method, data in result["models"].items()
        for p in data["points"]
    )
    destination.write_text(
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
        "<title>Laboratório AgiPrevê</title><h1>Comparação de baselines</h1>"
        "<p>Dados fictícios. MAE calculado na validação temporal; holdout excluído.</p>"
        "<table><tr><th>Baseline</th><th>MAE saldo (R$)</th></tr>" + rows + "</table>"
        "<table><tr><th>Data</th><th>Baseline</th><th>Saldo previsto</th></tr>"
        + daily
        + "</table></html>"
    )
    destination.with_suffix(".json").write_text(json.dumps(result, default=str, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", type=UUID, required=True)
    parser.add_argument("--cutoff", type=date.fromisoformat, required=True)
    parser.add_argument("--validation-end", type=date.fromisoformat, required=True)
    parser.add_argument("--horizon", type=int, choices=(7, 15, 30), default=7)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with Session(get_engine()) as session:
        rows = observations(session, args.account, args.validation_end)
        write_report(compare(rows, args.cutoff, args.horizon, args.validation_end), args.output)
