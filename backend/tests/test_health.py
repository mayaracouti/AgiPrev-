from unittest.mock import Mock

from sqlalchemy.exc import OperationalError

from app.db.session import get_session


def test_liveness_does_not_require_database(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_queries_database(client):
    session = Mock()
    client.app.dependency_overrides[get_session] = lambda: session
    response = client.get("/health/ready")
    assert response.status_code == 200
    session.execute.assert_called_once()
    assert str(session.execute.call_args.args[0]) == "SELECT 1"


def test_readiness_hides_database_error_details(client):
    session = Mock()
    session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("private details"))
    client.app.dependency_overrides[get_session] = lambda: session
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert "private details" not in response.text


def test_root_and_versioned_health_contracts(client):
    session = Mock()
    client.app.dependency_overrides[get_session] = lambda: session
    for path in ("/health", "/api/v1/health"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
