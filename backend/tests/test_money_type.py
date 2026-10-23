from decimal import Decimal

from sqlalchemy.dialects import postgresql

from app.db.types import MONEY


def test_money_uses_postgresql_numeric_and_decimal():
    assert MONEY.compile(dialect=postgresql.dialect()) == "NUMERIC(18, 2)"
    assert MONEY.python_type is Decimal
    assert MONEY.asdecimal is True
