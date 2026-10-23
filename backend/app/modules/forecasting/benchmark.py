"""CPU benchmark of real projection for 1000 synthetic clients; no HTTP/DB claim."""

import argparse
import json
import math
import os
import platform
import time
from pathlib import Path

from app.modules.forecasting.engine import project, train_expense_model
from app.modules.forecasting.pipeline import Observation
from app.modules.simulation.generator import ASOF, financial_rows


def customer(seed: int, index: int) -> list[Observation]:
    return [
        Observation(
            r["reference"],
            r["occurred_on"],
            r["occurred_on"],
            r["direction"],
            r["amount"],
            r["description"],
        )
        for r in financial_rows(seed, index)
    ]


def summary(seconds: list[float]) -> dict:
    ordered = sorted(seconds)
    return {
        "count": len(seconds),
        "p95_seconds": ordered[math.ceil(len(ordered) * 0.95) - 1],
        "max_seconds": max(ordered),
        "total_seconds": sum(ordered),
    }


def run(count: int = 1000, seed: int = 42) -> dict:
    if count < 1:
        raise ValueError("Positive client count required")
    started = time.perf_counter()
    model = train_expense_model(customer(seed, 0), ASOF)
    training = time.perf_counter() - started
    if model is None:
        raise ValueError("Training fixture must produce a model")
    inference, recalculation = [], []
    checksum = 0
    for index in range(count):
        rows = customer(seed, index)
        started = time.perf_counter()
        result = project(rows, ASOF, 30, expense_model=model)
        inference.append(time.perf_counter() - started)
        # Confirmed fictitious outgoing transfer becomes another available observation.
        rows.append(
            Observation(
                f"bench-pix:{index}",
                ASOF,
                ASOF,
                "debit",
                result["points"][0]["expense"] + 1,
                "Pix fictício",
            )
        )
        started = time.perf_counter()
        after = project(rows, ASOF, 30, expense_model=model)
        recalculation.append(time.perf_counter() - started)
        checksum += len(after["points"])
    return {
        "seed": seed,
        "clients": count,
        "horizon": 30,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
        },
        "scope": (
            "Sequential CPU projection and recalculation using pretrained model. "
            "Excludes HTTP, PostgreSQL, queuing, device rendering and per-client "
            "retraining; not E2E latency."
        ),
        "training_seconds_one_client": training,
        "model_version": model.version,
        "trained_through": str(model.trained_through),
        "inference": summary(inference),
        "recalculation": summary(recalculation),
        "point_checksum": checksum,
        "p95_cpu_within_2_seconds": max(
            summary(inference)["p95_seconds"], summary(recalculation)["p95_seconds"]
        )
        <= 2,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("/tmp/agipreve-performance.json"))
    args = parser.parse_args()
    report = run(args.count, args.seed)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
