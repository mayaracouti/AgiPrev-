def test_missing_token_invalid_login_body_and_unknown_route_are_structured(client):
    assert client.get("/api/v1/accounts").status_code == 401
    response = client.post("/api/v1/auth/login", json={"password": "private-demo-password"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "private-demo-password" not in response.text
    assert response.json()["request_id"]
    assert response.headers["x-request-id"]
    response = client.get("/unknown")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "HTTP_404"


def test_openapi_exposes_money_as_string_and_bearer_security(client):
    schema = client.get("/openapi.json").json()
    assert "/api/v1/accounts/{account_id}/balance" in schema["paths"]
    assert schema["components"]["schemas"]["BalanceResponse"]["properties"]["balance"]["type"] == "string"
    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
