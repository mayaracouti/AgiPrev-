import pytest
from alembic import command
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

pytestmark = pytest.mark.integration


def test_clean_schema_upgrade_downgrade_upgrade(pg_engine):
    engine, config = pg_engine
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        assert MigrationContext.configure(connection).get_current_revision() == "0004_forecasts"
        columns = inspect(connection).get_columns("ledger_entries")
        amount = next(column for column in columns if column["name"] == "amount")
        assert amount["type"].precision == 18 and amount["type"].scale == 2
        command.downgrade(config, "base")
        assert "customers" not in inspect(connection).get_table_names()
        command.upgrade(config, "head")
        assert "accounts" in inspect(connection).get_table_names()
        assert connection.scalar(text("SELECT count(*) FROM ledger_entries")) == 0


def test_upgrade_preserves_existing_ledger_and_classifies_old_rows(pg_engine):
    from sqlalchemy.orm import Session

    from app.seed import seed

    engine, config = pg_engine
    with Session(engine) as session:
        seed(session, "demo-test-only-2026")
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        before = connection.execute(text("SELECT id, amount FROM ledger_entries ORDER BY id")).all()
        command.downgrade(config, "0002_accounts_auth_ledger")
        command.upgrade(config, "head")
        after = connection.execute(text("SELECT id, amount FROM ledger_entries ORDER BY id")).all()
        assert before == after and len(after) == 3
        assert (
            connection.scalar(
                text("SELECT count(*) FROM ledger_entries WHERE category_id = 'income'")
            )
            == 3
        )
