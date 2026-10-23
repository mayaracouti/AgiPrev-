"""Append-only forecast snapshots and daily financial points."""

import sqlalchemy as sa
from alembic import op

revision = "0004_forecasts"
down_revision = "0003_transactions_scenarios"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ledger_entries", sa.Column("available_on", sa.Date(), nullable=True))
    op.add_column("ledger_entries", sa.Column("reversal_of", sa.String(100), nullable=True))
    op.create_foreign_key(
        "fk_ledger_reversal", "ledger_entries", "ledger_entries", ["reversal_of"], ["reference"]
    )
    # Existing rows are synthetic economic history, available on their simulated date.
    op.execute("UPDATE ledger_entries SET available_on = occurred_on")
    op.create_table(
        "forecast_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("base_date", sa.Date(), nullable=False),
        sa.Column("horizon", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(24), nullable=False),
        sa.Column("model_version", sa.String(80), nullable=False),
        sa.Column("dataset_version", sa.String(64), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_forecast_runs_account_id", "forecast_runs", ["account_id"])
    op.create_table(
        "forecast_points",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("forecast_runs.id"), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("income", sa.Numeric(18, 2), nullable=False),
        sa.Column("expense", sa.Numeric(18, 2), nullable=False),
        sa.Column("balance", sa.Numeric(18, 2), nullable=False),
        sa.UniqueConstraint("run_id", "day", name="uq_forecast_points_run_id"),
    )
    op.create_index("ix_forecast_points_run_id", "forecast_points", ["run_id"])
    op.execute("""CREATE FUNCTION reject_forecast_mutation() RETURNS trigger AS $$
    BEGIN RAISE EXCEPTION 'Forecast snapshots are immutable'; END;
    $$ LANGUAGE plpgsql""")
    for table in ("forecast_runs", "forecast_points"):
        op.execute(
            f"CREATE TRIGGER immutable_snapshot BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION reject_forecast_mutation()"
        )


def downgrade():
    op.drop_table("forecast_points")
    op.drop_table("forecast_runs")
    op.execute("DROP FUNCTION reject_forecast_mutation()")
    op.drop_constraint("fk_ledger_reversal", "ledger_entries", type_="foreignkey")
    op.drop_column("ledger_entries", "reversal_of")
    op.drop_column("ledger_entries", "available_on")
