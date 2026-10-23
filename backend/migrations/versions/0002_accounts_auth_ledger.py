"""Customers, accounts, immutable ledger references and revocable demo sessions."""
from alembic import op
import sqlalchemy as sa

revision = "0002_accounts_auth_ledger"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def identity_columns():
    return [sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.func.now())]


def upgrade() -> None:
    op.create_table(
        "customers", *identity_columns(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(160), nullable=False, unique=True),
        sa.Column("demo_profile", sa.String(24), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(256), nullable=False),
    )
    op.create_table(
        "accounts", *identity_columns(),
        sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.CheckConstraint("currency = 'BRL'", name="currency_brl"),
    )
    op.create_table(
        "ledger_entries", *identity_columns(),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("direction", sa.String(6), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2, asdecimal=True), nullable=False),
        sa.Column("description", sa.String(120), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("reference", sa.String(100), nullable=False, unique=True),
        sa.CheckConstraint("amount > 0", name="amount_positive"),
        sa.CheckConstraint("direction IN ('credit', 'debit')", name="direction_valid"),
    )
    op.create_index("ix_ledger_entries_account_id", "ledger_entries", ["account_id"])
    op.create_table(
        "auth_sessions", *identity_columns(),
        sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_auth_sessions_customer_id", "auth_sessions", ["customer_id"])


def downgrade() -> None:
    op.drop_table("auth_sessions")
    op.drop_table("ledger_entries")
    op.drop_table("accounts")
    op.drop_table("customers")
