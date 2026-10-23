"""Immutable reproducible evaluation experiments."""

import sqlalchemy as sa
from alembic import op

revision = "0005_evaluation"
down_revision = "0004_forecasts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "experiments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint("account_id", "fingerprint"),
    )
    op.create_index("ix_experiments_account_id", "experiments", ["account_id"])
    op.execute(
        "CREATE TRIGGER immutable_experiment BEFORE UPDATE OR DELETE ON experiments "
        "FOR EACH ROW EXECUTE FUNCTION reject_forecast_mutation()"
    )


def downgrade():
    op.drop_table("experiments")
