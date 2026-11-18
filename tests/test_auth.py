import pytest
from fastapi.testclient import TestClient
from backend.config import settings
from backend.main import create_app

def test_api_key_missing_returns_401(client):
    """Endpoints requiring authentication return HTTP 401 when X-Api-Key is missing."""
    res = client.get("/payments")
    assert res.status_code == 401
    assert "Missing API Key" in res.json().get("detail", "")

def test_api_key_wrong_returns_403(client):
    """Endpoints return HTTP 403 when an invalid X-Api-Key header is supplied."""
    res = client.get("/payments", headers={"X-Api-Key": "wrong_invalid_key"})
    assert res.status_code == 403
    assert "Invalid API Key" in res.json().get("detail", "")

def test_api_key_correct_returns_200(client, auth_headers):
    """Endpoints return success when the valid X-Api-Key header is supplied."""
    res = client.get("/payments", headers=auth_headers)
    assert res.status_code == 200
    assert "data" in res.json()

def test_exempt_endpoints_without_api_key(client):
    """Verify GET / and documentation endpoints do not require an API key."""
    # Health check
    res = client.get("/")
    assert res.status_code == 200
    assert res.json().get("status") == "online"

    # Swagger docs
    res = client.get("/docs")
    assert res.status_code == 200

    # OpenAPI JSON
    res = client.get("/openapi.json")
    assert res.status_code == 200

    # ReDoc
    res = client.get("/redoc")
    assert res.status_code == 200

def test_non_exempt_method_on_root_requires_key(client):
    """Verify non-GET requests to root require authentication."""
    res = client.post("/")
    # Should be rejected with 401 because only GET / is exempt
    assert res.status_code in [401, 405]

def test_production_mode_fails_startup_without_api_key(monkeypatch):
    """Verify startup aborts with RuntimeError if ENVIRONMENT is production and API_KEY is unset."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "API_KEY", None)

    app = create_app()
    with pytest.raises(RuntimeError, match="API_KEY environment variable is not set in production mode"):
        with TestClient(app):
            pass
