from fastapi.testclient import TestClient
from backend.config import settings
from backend.main import create_app

def test_cors_allowed_origin(monkeypatch):
    """Verify origin in CORS_ALLOWED_ORIGINS receives Access-Control-Allow-Origin header."""
    monkeypatch.setattr(settings, "CORS_ALLOWED_ORIGINS", "http://allowed.test,http://localhost:3000")
    monkeypatch.setattr(settings, "API_KEY", "test_key")
    app = create_app()
    client = TestClient(app)

    # Allowed origin GET / (exempt from auth)
    res = client.get("/", headers={"Origin": "http://allowed.test"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://allowed.test"
    assert res.headers.get("access-control-allow-credentials") == "true"

def test_cors_blocked_origin(monkeypatch):
    """Verify origin not listed in CORS_ALLOWED_ORIGINS is denied cross-origin headers."""
    monkeypatch.setattr(settings, "CORS_ALLOWED_ORIGINS", "http://allowed.test")
    monkeypatch.setattr(settings, "API_KEY", "test_key")
    app = create_app()
    client = TestClient(app)

    res = client.get("/", headers={"Origin": "http://blocked.test"})
    assert res.status_code == 200
    assert "access-control-allow-origin" not in res.headers

def test_cors_unset_default_no_cross_origin(monkeypatch):
    """Verify that when CORS_ALLOWED_ORIGINS is unset or empty, cross-origin access is denied."""
    monkeypatch.setattr(settings, "CORS_ALLOWED_ORIGINS", "")
    monkeypatch.setattr(settings, "API_KEY", "test_key")
    app = create_app()
    client = TestClient(app)

    res = client.get("/", headers={"Origin": "http://any-domain.test"})
    assert res.status_code == 200
    assert "access-control-allow-origin" not in res.headers

def test_cors_wildcard_never_with_credentials(monkeypatch):
    """Verify that if wildcard '*' is used in allowed origins, credentials are never allowed."""
    monkeypatch.setattr(settings, "CORS_ALLOWED_ORIGINS", "*")
    monkeypatch.setattr(settings, "API_KEY", "test_key")
    app = create_app()
    client = TestClient(app)

    res = client.get("/", headers={"Origin": "http://any-domain.test"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "*"
    assert res.headers.get("access-control-allow-credentials") != "true"
