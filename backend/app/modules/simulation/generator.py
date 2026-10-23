"""Versioned, deterministic fictitious financial data. No external data sources."""

import argparse
import random
from datetime import date, timedelta
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import insert, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import get_engine
from app.modules.banking.models import Account, Customer, LedgerEntry
from app.modules.simulation.models import Scenario, ScheduledEvent

VERSION = "synthetic-v1"
ASOF = date(2026, 10, 23)
PROFILES = ("regular", "variable", "tight", "retired", "entrepreneur", "seasonal")
SALARIES = (400000, 520000, 180000, 280000, 720000, 350000)


def identifier(seed, index, label):
    return uuid5(NAMESPACE_URL, f"{VERSION}:{seed}:{index}:{label}")


def financial_rows(seed: int, index: int):
    """12 months of labeled monthly series plus nonperiodic, varied daily expenses."""
    rng = random.Random(f"{VERSION}:{seed}:{index}")
    profile = PROFILES[index % 6]
    salary = SALARIES[index % 6]
    account_id = identifier(seed, index, "account")
    start = ASOF - timedelta(days=365)
    rows = []
    for delta in range(365):
        day = start + timedelta(days=delta)
        base = {"account_id": account_id, "occurred_on": day, "kind": "synthetic"}
        monthly = {
            5: ("credit", salary, "income", "Salário fictício", "salary"),
            8: ("debit", salary * 30 // 100, "housing", "Aluguel fictício", "rent"),
            15: ("debit", 2990, "subscriptions", "Assinatura fictícia", "subscription"),
        }
        if day.day in monthly:
            direction, cents, category, description, label = monthly[day.day]
            # Variable/seasonal incomes vary more, exposing limits of the fixed-value detector.
            if label == "salary" and profile in ("variable", "seasonal"):
                cents = cents * rng.randint(75, 125) // 100
            rows.append(
                {
                    **base,
                    "id": identifier(seed, index, f"{day}:{label}"),
                    "direction": direction,
                    "amount": Decimal(cents) / 100,
                    "category_id": category,
                    "description": description,
                    "reference": f"syn:{seed}:{index}:{day}:{label}",
                }
            )
        if delta % 3 == 0:
            cents = rng.randint(1500, 8500)
            rows.append(
                {
                    **base,
                    "id": identifier(seed, index, f"{day}:purchase"),
                    "direction": "debit",
                    "amount": Decimal(cents) / 100,
                    "category_id": "food",
                    "description": "Mercado fictício",
                    "reference": f"syn:{seed}:{index}:{day}:purchase",
                }
            )
    return rows


def future_rows(seed, index, scenario_id):
    salary = SALARIES[index % 6]
    rows = []
    # A full year of pending events; these are never exposed as realized transactions.
    for offset in range(13):
        month_index = ASOF.year * 12 + ASOF.month - 1 + offset
        year, month = divmod(month_index, 12)
        for day, direction, cents, category, description, kind in (
            (5, "credit", salary, "income", "Salário fictício", "salary"),
            (8, "debit", salary * 30 // 100, "housing", "Aluguel fictício", "rent"),
            (15, "debit", 2990, "subscriptions", "Assinatura fictícia", "subscription"),
        ):
            scheduled = date(year, month + 1, day)
            if ASOF < scheduled <= ASOF + timedelta(days=366):
                rows.append(
                    {
                        "id": uuid5(NAMESPACE_URL, f"{scenario_id}:pending:{scheduled}:{kind}"),
                        "scenario_id": scenario_id,
                        "scheduled_on": scheduled,
                        "original_date": scheduled,
                        "direction": direction,
                        "amount": Decimal(cents) / 100,
                        "category_id": category,
                        "description": description,
                        "kind": kind,
                        "processed": False,
                    }
                )
    return rows


def generate(session: Session, seed=42, count=1000, password=None):
    if not 1 <= count <= 10000 or not 0 <= seed <= 2147483647:
        raise ValueError("count must be 1..10000 and seed 0..2147483647")
    # Serialize generator runs; all writes commit together, safe on retry/failure.
    session.execute(text("SELECT pg_advisory_xact_lock(1701820)"))
    existing = set(
        session.scalars(
            select(Customer.id).where(Customer.email.like(f"synthetic-{seed}-%@demo.local"))
        )
    )
    customers, accounts, scenarios, events, entries = [], [], [], [], []
    for index in range(count):
        customer_id = identifier(seed, index, "customer")
        if customer_id in existing:
            continue  # Never overwrite an account already used in a demonstration.
        account_id = identifier(seed, index, "account")
        scenario_id = identifier(seed, index, "scenario")
        customers.append(
            {
                "id": customer_id,
                "name": f"Cliente fictício {index + 1:04d}",
                "email": f"synthetic-{seed}-{index}@demo.local",
                "demo_profile": PROFILES[index % 6],
                "password_hash": hash_password(password)
                if password
                else "disabled-synthetic-login",
            }
        )
        accounts.append({"id": account_id, "customer_id": customer_id, "currency": "BRL"})
        scenarios.append(
            {
                "id": scenario_id,
                "account_id": account_id,
                "current_date": ASOF,
                "seed": seed,
                "version": VERSION,
            }
        )
        entries.extend(financial_rows(seed, index))
        events.extend(future_rows(seed, index, scenario_id))
    if customers:
        session.execute(insert(Customer), customers)
        session.execute(insert(Account), accounts)
        session.execute(insert(Scenario), scenarios)
        for batch in range(0, len(entries), 5000):
            session.execute(insert(LedgerEntry), entries[batch : batch + 5000])
        session.execute(insert(ScheduledEvent), events)
    session.commit()
    return {
        "version": VERSION,
        "seed": seed,
        "created_customers": len(customers),
        "created_transactions": len(entries),
        "created_pending_events": len(events),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--count", type=int, default=1000)
    args = parser.parse_args()
    settings = get_settings()
    if settings.app_env != "development" or settings.demo_password is None:
        raise SystemExit("Configure development and DEMO_PASSWORD; no real credentials.")
    with Session(get_engine()) as session:
        print(generate(session, args.seed, args.count, settings.demo_password.get_secret_value()))
