import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize(
    "values",
    [
        {"database_url": "sqlite:///wrong.db"},
        {"database_url": "postgresql://demo:demo@localhost/demo"},
        {"session_ttl_minutes": 0},
        {"session_ttl_minutes": 1441},
        {"cors_origins": ["*"]},
        {"demo_password": "short"},
    ],
)
def test_invalid_configuration_is_rejected(values):
    base = {"database_url": "postgresql+psycopg://demo:demo@localhost/agipreve_test"}
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{**base, **values})


def test_valid_configuration_and_password_repr():
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://demo:demo@localhost/agipreve_test",
        demo_password="demo-test-only-2026",
    )
    assert settings.session_ttl_minutes == 60
    assert "demo-test-only-2026" not in repr(settings)
