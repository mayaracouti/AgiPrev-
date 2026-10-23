"""Durable alerts, rules and post-commit forecast recovery."""

import sqlalchemy as sa
from alembic import op

revision = "0006_alerts_refresh"
down_revision = "0005_evaluation"
branch_labels = None
depends_on = None


def identity():
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade():
    op.create_table(
        "alert_rules",
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("critical_days", sa.Integer(), nullable=False),
    )
    op.create_table(
        "alerts",
        *identity(),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("forecast_runs.id"), nullable=False),
        sa.Column("risk_date", sa.Date(), nullable=False),
        sa.Column("deficit", sa.Numeric(18, 2), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("message", sa.String(600), nullable=False),
        sa.Column("recommendation", sa.String(600), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("account_id", "risk_date", name="uq_alerts_account_id"),
    )
    op.create_index("ix_alerts_account_id", "alerts", ["account_id"])
    op.create_table(
        "forecast_refreshes",
        *identity(),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column(
            "transaction_id",
            sa.Uuid(),
            sa.ForeignKey("ledger_entries.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("previous_forecast_id", sa.Uuid(), sa.ForeignKey("forecast_runs.id")),
        sa.Column("forecast_id", sa.Uuid(), sa.ForeignKey("forecast_runs.id")),
        sa.Column("error_code", sa.String(40)),
    )
    op.create_index("ix_forecast_refreshes_account_id", "forecast_refreshes", ["account_id"])


def downgrade():
    op.drop_table("forecast_refreshes")
    op.drop_table("alerts")
    op.drop_table("alert_rules")
