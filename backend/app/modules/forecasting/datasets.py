"""Export versioned chronological partitions; holdout is never returned to model selection."""

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from app.modules.forecasting.pipeline import aggregate, eligible, temporal_split
from app.modules.forecasting.router import observations


def export_dataset(
    series,
    train_end: date,
    validation_end: date,
    destination: Path,
    horizon: int = 30,
    seed: int = 42,
    source_rows: list | None = None,
) -> dict:
    split = temporal_split(series, train_end, validation_end, horizon, seed)
    if source_rows is not None:
        canonical = json.dumps(
            [asdict(r) for r in sorted(source_rows, key=lambda r: r.reference)],
            default=str,
            sort_keys=True,
        )
        split["version"] = hashlib.sha256((split["version"] + canonical).encode()).hexdigest()
    directory = destination / split["version"]
    directory.mkdir(parents=True, exist_ok=True)
    partitions = {**split["selection"], "final_holdout": split["final_holdout"]}
    for name, rows in partitions.items():
        if source_rows is None:
            payload = [asdict(r) for r in rows]
        else:
            boundary = (
                train_end
                if name == "train"
                else validation_end
                if name == "validation"
                else max(r.day for r in series)
            )
            known = eligible(source_rows, boundary)
            available_series = {
                r.day: r for r in aggregate(known, min(r.day for r in series), boundary)
            }
            payload = {
                "series": [asdict(available_series[r.day]) for r in rows],
                "observations": [asdict(r) for r in known],
            }
        content = json.dumps(payload, default=str, sort_keys=True)
        path = directory / (name + ".json")
        if path.exists() and path.read_text() != content:
            raise ValueError("Version collision: dataset is immutable")
        path.write_text(content)
    manifest = {k: v for k, v in split.items() if k not in ("selection", "final_holdout")}
    manifest.update(
        train_end=str(train_end),
        validation_end=str(validation_end),
        holdout_policy="final evaluation only; excluded from model selection",
    )
    (directory / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
    return manifest


if __name__ == "__main__":
    from uuid import UUID

    from sqlalchemy.orm import Session

    from app.db.session import get_engine

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", type=UUID, required=True)
    parser.add_argument("--cutoff", type=date.fromisoformat, required=True)
    parser.add_argument("--train-end", type=date.fromisoformat, required=True)
    parser.add_argument("--validation-end", type=date.fromisoformat, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    with Session(get_engine()) as session:
        rows = observations(session, args.account, args.cutoff)
        if not rows:
            raise SystemExit("No realized history")
        series = aggregate(rows, min(r.occurred_on for r in rows), args.cutoff)
        print(
            export_dataset(
                series,
                args.train_end,
                args.validation_end,
                args.destination,
                seed=args.seed,
                source_rows=rows,
            )
        )
