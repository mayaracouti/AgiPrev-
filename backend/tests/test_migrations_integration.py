import pytest
from alembic import command
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

pytestmark = pytest.mark.integration


def test_clean_schema_upgrade_downgrade_upgrade(pg_engine):
    engine, config = pg_engine
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        assert MigrationContext.configure(connection).get_current_revision() == "0002_accounts_auth_ledger"
        columns = inspect(connection).get_columns("ledger_entries")
        amount = next(column for column in columns if column["name"] == "amount")
        assert amount["type"].precision == 18 and amount["type"].scale == 2
        command.downgrade(config, "base")
        assert "customers" not in inspect(connection).get_table_names()
        command.upgrade(config, "head")
        assert "accounts" in inspect(connection).get_table_names()
        assert connection.scalar(text("SELECT count(*) FROM ledger_entries")) == 0
