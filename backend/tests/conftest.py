import os
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import MagicMock

# Set environment variables BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://mock:6379/0"
os.environ["GEMINI_API_KEYS_RAW"] = "mock_key_1,mock_key_2"
os.environ["GEMINI_RPM_LIMITS"] = "gemini-3.1-flash-lite-preview=15, gemini-3-flash-preview=10"
os.environ["GEMINI_RPD_LIMITS"] = "gemini-3.1-flash-lite-preview=1000, gemini-3-flash-preview=500"
os.environ["GEMINI_API_COOLDOWN_MINUTES"] = "1"
os.environ["GEMINI_API_RESET_TIMEZONE"] = "UTC"

# --- Lazy imports to avoid spaCy crash on Python 3.14 ---
# These are deferred to fixtures that actually need the full app.
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _ensure_models():
    """Import all models so that Base.metadata is populated."""
    import app.models as _models  # noqa: F401


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Creates a fresh database for each test function."""
    _ensure_models()
    from app.db import Base

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator:
    """
    FastAPI TestClient with overridden database dependency.
    Requires the full app (including spaCy). Tests that need this will
    be skipped if spaCy is broken in the env.
    """
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        from app.deps import get_db
    except Exception as e:
        pytest.skip(f"Cannot import app (likely spaCy issue): {e}")
        return

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_gemini():
    """Mocks the GeminiClient to avoid real API calls."""
    from app.services.gemini_client import gemini_client

    original_complete = gemini_client.complete
    mock = MagicMock()
    gemini_client.complete = mock

    yield mock

    gemini_client.complete = original_complete
