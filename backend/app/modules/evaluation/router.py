import csv
import hashlib
import html
import io
import json
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from sqlalchemy import select

from app.core.errors import AppError
from app.modules.auth.dependencies import CurrentCustomer, Database
from app.modules.banking.transaction_router import owned_locked
from app.modules.evaluation.models import Experiment
from app.modules.evaluation.service import dataset_digest, evaluate
from app.modules.forecasting.router import observations
from app.modules.simulation.services import get_scenario

router = APIRouter(prefix="/accounts/{account_id}", tags=["evaluation"])


class EvaluationInput(BaseModel):
    train_end: date
    validation_end: date
    final_end: date
    seed: int = 42


@router.post("/experiments")
def create_experiment(
    account_id: UUID, body: EvaluationInput, session: Database, customer: CurrentCustomer
):
    owned_locked(session, account_id, customer.id)
    if body.final_end > get_scenario(session, account_id).current_date:
        raise AppError(
            422, "UNREALIZED_EVALUATION", "O holdout deve conter somente datas realizadas."
        )
    rows = observations(session, account_id, body.final_end)
    canonical = json.dumps(
        {
            "config": body.model_dump(mode="json"),
            "rows": [repr(r) for r in rows],
            "engine": "evaluation-v1",
        },
        sort_keys=True,
    )
    fingerprint = hashlib.sha256(canonical.encode()).hexdigest()
    existing = session.scalar(
        select(Experiment).where(
            Experiment.account_id == account_id, Experiment.fingerprint == fingerprint
        )
    )
    if existing:
        return {"id": str(existing.id), **existing.payload}
    dataset_version = dataset_digest(rows, body.final_end)
    previous = session.scalars(select(Experiment).where(Experiment.account_id == account_id))
    if any(r.payload.get("dataset_version") == dataset_version for r in previous):
        raise AppError(
            409,
            "FINAL_HOLDOUT_LOCKED",
            "O holdout deste dataset já foi avaliado; a seleção não pode ser alterada.",
        )
    try:
        result = evaluate(rows, body.train_end, body.validation_end, body.final_end, body.seed)
    except ValueError as exc:
        raise AppError(422, "INVALID_EVALUATION", str(exc)) from exc
    result["profile"] = customer.demo_profile
    experiment = Experiment(
        account_id=account_id,
        fingerprint=fingerprint,
        payload=json.loads(json.dumps(result, default=str)),
    )
    session.add(experiment)
    session.commit()
    return {"id": str(experiment.id), **experiment.payload}


@router.get("/experiments")
def list_experiments(account_id: UUID, session: Database, customer: CurrentCustomer):
    owned_locked(session, account_id, customer.id)
    return [
        {"id": str(r.id), **r.payload}
        for r in session.scalars(
            select(Experiment)
            .where(Experiment.account_id == account_id)
            .order_by(Experiment.created_at.desc())
            .limit(100)
        )
    ]


@router.get("/evaluation/reports")
def reports(
    account_id: UUID,
    session: Database,
    customer: CurrentCustomer,
    format: str = Query("json", pattern="^(json|csv|html)$"),
    model: str | None = None,
    horizon: int | None = None,
    partition: str | None = None,
    profile: str | None = None,
):
    experiments = list_experiments(account_id, session, customer)
    records = [
        {
            "experiment_id": e["id"],
            "experiment_version": e["experiment_version"],
            "dataset_version": e["dataset_version"],
            "profile": e["profile"],
            **r,
        }
        for e in experiments
        if profile is None or e["profile"] == profile
        for r in e["records"]
        if (model is None or r["model"] == model)
        and (horizon is None or r["horizon"] == horizon)
        and (partition is None or r["partition"] == partition)
    ]
    if format == "json":
        return {"records": records, "notice": "Dados fictícios; avaliação temporal calculada."}
    columns = [
        "experiment_id",
        "experiment_version",
        "dataset_version",
        "profile",
        "partition",
        "model",
        "horizon",
        "model_version",
        "mae",
        "mse",
        "rmse",
        "bias",
        "precision",
        "recall",
        "f1",
        "f2",
        "lead_time_days",
    ]
    flat = [{**{k: r[k] for k in columns[:8]}, **r["metrics"]} for r in records]
    if format == "csv":
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flat)
        return Response(
            out.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="evaluation.csv"'},
        )

    def attributes(row):
        return " ".join(
            "data-" + key + '="' + html.escape(str(row[key]), quote=True) + '"'
            for key in ("model", "horizon", "profile", "partition")
        )

    controls = "".join(
        "<label>" + label + ' <select data-filter="' + key + '">'
        '<option value="">Todos</option>'
        + "".join(
            "<option>" + html.escape(value) + "</option>"
            for value in sorted({str(row[key]) for row in records})
        )
        + "</select></label> "
        for key, label in (
            ("model", "Modelo"),
            ("horizon", "Horizonte"),
            ("profile", "Perfil"),
            ("partition", "Partição"),
        )
    )
    table = "".join(
        "<tr data-record "
        + attributes(r)
        + ">"
        + "".join("<td>" + html.escape(str(r.get(c, ""))) + "</td>" for c in columns)
        + "</tr>"
        for r in flat
    )
    charts = "".join(
        "<figure data-record "
        + attributes(r)
        + "><figcaption>"
        + html.escape(r["model"] + " / " + str(r["horizon"]) + " dias / " + r["partition"])
        + '</figcaption><svg viewBox="0 0 300 100" role="img" '
        'aria-label="MAE em reais"><rect x="0" y="10" width="'
        + str(min(290, float(r["metrics"]["mae"])))
        + '" height="20" fill="#2860cc"/></svg></figure>'
        for r in records
    )
    return HTMLResponse(
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
        "<title>Laboratório AgiPrevê</title>"
        "<h1>Avaliação temporal</h1><p>Dados fictícios. "
        "Filtros locais sobre os registros autorizados. "
        "Barras: MAE em reais (escala máxima 290).</p>"
        + controls
        + "<table><tr>"
        + "".join("<th>" + c + "</th>" for c in columns)
        + "</tr>"
        + table
        + "</table>"
        + charts
        + """<script>
        const filters = [...document.querySelectorAll('[data-filter]')];
        for (const filter of filters) filter.addEventListener('change', () => {
          for (const row of document.querySelectorAll('[data-record]')) {
            row.hidden = filters.some(f => f.value && row.dataset[f.dataset.filter] !== f.value);
          }
        });
        </script></html>"""
    )
