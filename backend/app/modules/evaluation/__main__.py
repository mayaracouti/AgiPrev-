"""Offline reproducible evaluation; never reads real banking data."""

import argparse
import json
from datetime import date
from pathlib import Path

from app.modules.evaluation.service import evaluate
from app.modules.forecasting.pipeline import Observation
from app.modules.simulation.generator import financial_rows

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    print(json.dumps({"reused": True, "path": str(args.output)}))
    raise SystemExit(0)
reports = []
for index in range(6):
    rows = [
        Observation(
            r["reference"],
            r["occurred_on"],
            r["occurred_on"],
            r["direction"],
            r["amount"],
            r["description"],
        )
        for r in financial_rows(42, index)
    ]
    reports.append(
        {
            "synthetic_profile_index": index,
            **evaluate(rows, date(2026, 7, 1), date(2026, 8, 1), date(2026, 9, 1)),
        }
    )
args.output.write_text(json.dumps({"reports": reports}, sort_keys=True, indent=2))
print(
    json.dumps(
        {
            "profiles": len(reports),
            "records": sum(len(r["records"]) for r in reports),
            "path": str(args.output),
        }
    )
)
