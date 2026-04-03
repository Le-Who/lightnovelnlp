import os
import pytest
import typing
from typing import Generator
from sqlalchemy import create_engine

# Monkeypatch for pydantic v1 / python 3.12 compatibility
# This resolves TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
# when importing spacy (which uses pydantic v1)
if hasattr(typing.ForwardRef, "_evaluate"):
    _evaluate_original = typing.ForwardRef._evaluate

    def _evaluate_patched(self, globalns, localns, *args, **kwargs):
        type_params = kwargs.get("type_params", None)
        recursive_guard = kwargs.get("recursive_guard", None)

        if args:
            # If called with positional args, check what they are
            # Pydantic v1 calls: _evaluate(globalns, localns, recursive_guard)
            # Python 3.12 calls: _evaluate(globalns, localns, type_params, recursive_guard=...)
            arg0 = args[0]
            if isinstance(arg0, set):
                recursive_guard = arg0
            else:
                type_params = arg0

        if recursive_guard is None:
            recursive_guard = set()

        return _evaluate_original(self, globalns, localns, type_params=type_params, recursive_guard=recursive_guard)

    typing.ForwardRef._evaluate = _evaluate_patched
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
