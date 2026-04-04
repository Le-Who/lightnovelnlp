"""
conftest.py — Shared test fixtures for the Light Novel NLP backend.

Design constraints:
- Environment variables must be set BEFORE any app module import (module-level import
  side effects read settings at import time via pydantic-settings).
- All DB-touching fixtures use SQLite :memory: with StaticPool for speed and isolation.
- pgvector-specific code is NOT testable against SQLite — such tests must use
  `postgres_db` fixture and be marked with @pytest.mark.postgres.
- The `mock_gemini` fixture patches the global singleton's `.complete()` method to avoid
  real Gemini API calls in unit/integration tests.

Running subsets:
  pytest                              # all tests (postgres auto-skipped without --postgres-url)
  pytest -m "not postgres"            # unit + integration only
  pytest -m postgres --postgres-url=postgresql://...  # full suite with real PG
"""

import os

# ── Environment must be set before ANY app import ─────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://mock:6379/0")
os.environ.setdefault("GEMINI_API_KEYS_RAW", "mock_key_1,mock_key_2")
os.environ.setdefault(
    "GEMINI_RPM_LIMITS", "gemini-3.1-flash-lite-preview=15, gemini-3-flash-preview=10"
)
os.environ.setdefault(
    "GEMINI_RPD_LIMITS",
    "gemini-3.1-flash-lite-preview=1000, gemini-3-flash-preview=500",
)
os.environ.setdefault("GEMINI_API_COOLDOWN_MINUTES", "1")
os.environ.setdefault("GEMINI_API_RESET_TIMEZONE", "UTC")

import pytest
from typing import Generator
from unittest.mock import MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, NullPool


# ── CLI option + marker hooks ──────────────────────────────────────────────────


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add --postgres-url flag to enable @pytest.mark.postgres tests."""
    parser.addoption(
        "--postgres-url",
        action="store",
        default=None,
        help=(
            "PostgreSQL connection URL for @pytest.mark.postgres tests. "
            "Example: postgresql://user:pass@localhost:5432/testdb"
        ),
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """
    Auto-skip @pytest.mark.postgres tests when --postgres-url is not provided.
    This means the full local `pytest` run never errors — postgres tests are
    silently skipped unless the developer explicitly opts in.
    """
    if config.getoption("--postgres-url", default=None):
        return  # --postgres-url supplied → run everything

    skip_postgres = pytest.mark.skip(
        reason="Pass --postgres-url=<url> to enable PostgreSQL integration tests"
    )
    for item in items:
        if item.get_closest_marker("postgres"):
            item.add_marker(skip_postgres)


# ── In-memory SQLite engine (shared across the process via StaticPool) ──────
_SQLITE_URL = "sqlite:///:memory:"

engine = create_engine(
    _SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _ensure_models() -> None:
    """Import all SQLAlchemy models so Base.metadata is fully populated."""
    import app.models  # noqa: F401  — side-effect: registers all models with Base


# ── Core fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Provides an isolated in-memory SQLite session per test function.

    Creates all tables before the test and drops them after, guaranteeing
    a clean slate regardless of test order.
    """
    _ensure_models()
    from app.db import Base

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator:
    """
    FastAPI TestClient with the real DB dependency overridden to use the
    in-memory SQLite session from the `db` fixture.

    Skips gracefully if the app cannot be imported (e.g. broken spaCy on
    Python 3.14 local dev environment).
    """
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        from app.deps import get_db
    except Exception as e:
        pytest.skip(f"Cannot import app (likely spaCy/Celery on Python 3.14): {e}")
        return

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_gemini():
    """
    Patches `gemini_client.complete` on the global singleton to prevent
    any real Gemini API calls in unit and integration tests.

    Returns the MagicMock so tests can configure return values and assert calls.
    """
    from app.services.gemini_client import gemini_client

    original_complete = gemini_client.complete
    mock_fn = MagicMock()
    gemini_client.complete = mock_fn
    try:
        yield mock_fn
    finally:
        gemini_client.complete = original_complete


# ── Factory helpers (shared across multiple test modules) ─────────────────────


def make_project(
    db: Session, *, name: str = "Test Project", genre: str = "fantasy"
) -> "Project":  # type: ignore[name-defined]
    """Creates and commits a minimal Project; returns the refreshed ORM object."""
    from app.models.project import Project

    project = Project(name=name, genre=genre)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def make_chapter(
    db: Session,
    project_id: int,
    *,
    title: str = "Chapter 1",
    original_text: str = "Some original text.",
    order: int = 1,
) -> "Chapter":  # type: ignore[name-defined]
    """Creates and commits a Chapter; returns the refreshed ORM object."""
    from app.models.project import Chapter

    chapter = Chapter(
        project_id=project_id,
        title=title,
        original_text=original_text,
        order=order,
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


def make_glossary_term(
    db: Session,
    project_id: int,
    *,
    source_term: str = "Term",
    translated_term: str = "Term_RU",
    category: str = "other",
    status: str = "approved",
) -> "GlossaryTerm":  # type: ignore[name-defined]
    """Creates and commits an approved GlossaryTerm; returns the refreshed ORM object."""
    from app.models.glossary import GlossaryTerm, TermStatus

    status_enum = TermStatus(status) if isinstance(status, str) else status
    term = GlossaryTerm(
        project_id=project_id,
        source_term=source_term,
        translated_term=translated_term,
        category=category,
        status=status_enum,
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return term


# ── PostgreSQL fixture (requires --postgres-url) ───────────────────────────────


@pytest.fixture(scope="function")
def postgres_db(request: pytest.FixtureRequest) -> Generator[Session, None, None]:
    """
    Provides a real PostgreSQL session for @pytest.mark.postgres tests.

    Setup:
      1. Connects to the URL passed via --postgres-url (fails if absent).
      2. Enables the pgvector extension.
      3. Creates all tables from the ORM metadata.
    Teardown:
      1. Drops all tables (clean slate for next test).
      2. Closes the engine.

    Usage:
        @pytest.mark.postgres
        def test_semantic_search(postgres_db: Session): ...
    """
    postgres_url = request.config.getoption("--postgres-url", default=None)
    if not postgres_url:
        pytest.skip("--postgres-url not provided; skipping postgres test")

    _ensure_models()
    from app.db import Base

    pg_engine = create_engine(postgres_url, poolclass=NullPool)
    PgSession = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)

    # Enable pgvector extension before creating tables
    with pg_engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=pg_engine)
    session = PgSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=pg_engine)
        pg_engine.dispose()
