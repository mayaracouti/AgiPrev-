"""Categories on the existing ledger, virtual scenarios and pending events."""

import sqlalchemy as sa
from alembic import op

revision = "0003_transactions_scenarios"
down_revision = "0002_accounts_auth_ledger"
branch_labels = None
depends_on = None

CATEGORIES = [
    ("income", "Renda"),
    ("housing", "Moradia"),
    ("food", "Alimentação"),
    ("transport", "Transporte"),
    ("health", "Saúde"),
    ("subscriptions", "Assinaturas"),
    ("pix", "Pix"),
    ("other", "Outros"),
]


def identity():
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def upgrade():
    op.create_table(
        "categories",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("name", sa.String(60), nullable=False),
    )
    table = sa.table("categories", sa.column("id", sa.String), sa.column("name", sa.String))
    op.bulk_insert(table, [{"id": key, "name": name} for key, name in CATEGORIES])
    op.add_column(
        "ledger_entries",
        sa.Column("category_id", sa.String(24), nullable=False, server_default="other"),
    )
    op.create_foreign_key(
        "fk_ledger_category", "ledger_entries", "categories", ["category_id"], ["id"]
    )
    op.add_column(
        "ledger_entries",
        sa.Column("kind", sa.String(16), nullable=False, server_default="transfer"),
    )
    op.add_column("ledger_entries", sa.Column("recipient", sa.String(120)))
    op.add_column("ledger_entries", sa.Column("request_hash", sa.String(64)))
    op.execute("UPDATE ledger_entries SET category_id='income' WHERE direction='credit'")
    op.create_index("ix_transactions_order", "ledger_entries", ["account_id", "occurred_on", "id"])
    op.drop_constraint("uq_customers_demo_profile", "customers", type_="unique")
    op.create_index("ix_customers_demo_profile", "customers", ["demo_profile"])
    op.create_table(
        "scenarios",
        *identity(),
        sa.Column(
            "account_id",
            sa.Uuid(),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("current_date", sa.Date(), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(24), nullable=False),
    )
    op.create_table(
        "scheduled_events",
        *identity(),
        sa.Column(
            "scenario_id",
            sa.Uuid(),
            sa.ForeignKey("scenarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scheduled_on", sa.Date(), nullable=False),
        sa.Column("original_date", sa.Date(), nullable=False),
        sa.Column("direction", sa.String(6), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("category_id", sa.String(24), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("description", sa.String(120), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False),
        sa.CheckConstraint("amount > 0", name="event_amount_positive"),
        sa.CheckConstraint("direction IN ('credit', 'debit')", name="event_direction_valid"),
    )
    op.create_index("ix_scheduled_events_scenario_id", "scheduled_events", ["scenario_id"])
    op.create_table(
        "scenario_actions",
        *identity(),
        sa.Column(
            "scenario_id",
            sa.Uuid(),
            sa.ForeignKey("scenarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("event_id", sa.Uuid(), sa.ForeignKey("scheduled_events.id"), nullable=False),
        sa.UniqueConstraint("scenario_id", "key"),
    )


def downgrade():
    # Six-profile datasets cannot fit the old one-customer-per-profile constraint.
    # Refuse the downgrade rather than destroying fictitious customers/history.
    bind = op.get_bind()
    if bind.scalar(
        sa.text(
            "SELECT count(*) FROM (SELECT demo_profile FROM customers "
            "GROUP BY demo_profile HAVING count(*) > 1) t"
        )
    ):
        raise RuntimeError("Downgrade requires a clean dataset: duplicate financial profiles exist")
    op.drop_table("scenario_actions")
    op.drop_table("scheduled_events")
    op.drop_table("scenarios")
    op.drop_index("ix_customers_demo_profile", table_name="customers")
    op.create_unique_constraint("uq_customers_demo_profile", "customers", ["demo_profile"])
    op.drop_index("ix_transactions_order", table_name="ledger_entries")
    op.drop_constraint("fk_ledger_category", "ledger_entries", type_="foreignkey")
    for column in ("request_hash", "recipient", "kind", "category_id"):
        op.drop_column("ledger_entries", column)
    op.drop_table("categories")
