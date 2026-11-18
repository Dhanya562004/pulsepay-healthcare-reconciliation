import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database.base import Base
from backend.database.session import get_db
import backend.database.session as db_session
from backend.config import settings
from backend.main import create_app

TEST_API_KEY = "test_phase1_api_key_xyz"

@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine with StaticPool for test isolation."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True)
def setup_test_db(test_engine, TestingSessionLocal, monkeypatch):
    """Recreate tables and set up test environment before each test."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Monkeypatch settings
    monkeypatch.setattr(settings, "API_KEY", TEST_API_KEY)
    monkeypatch.setattr(settings, "ENVIRONMENT", "test")
    monkeypatch.setattr(settings, "CORS_ALLOWED_ORIGINS", "http://allowed.test")

    # Monkeypatch database session
    monkeypatch.setattr(db_session, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(db_session, "engine", test_engine)

    yield

@pytest.fixture
def db(test_engine, TestingSessionLocal):
    """Yield a database session for direct test assertions."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def app(test_engine, TestingSessionLocal):
    """Create test FastAPI application instance with overridden get_db."""
    test_app = create_app()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    test_app.dependency_overrides[get_db] = override_get_db
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"X-Api-Key": TEST_API_KEY}
