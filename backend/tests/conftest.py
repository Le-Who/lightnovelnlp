import os
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import MagicMock

# Set environment variables BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://mock:6379/0"
os.environ["GEMINI_API_KEYS_RAW"] = '["mock_key"]'
os.environ["GEMINI_API_LIMIT_PER_KEY"] = "10"
os.environ["GEMINI_API_LIMIT_THRESHOLD_PERCENT"] = "90"
os.environ["GEMINI_API_COOLDOWN_HOURS"] = "1"
os.environ["GEMINI_API_RESET_TIMEZONE"] = "UTC"

from fastapi.testclient import TestClient
from app.main import app
from app.db import Base
from app.deps import get_db
from app.services.gemini_client import gemini_client
import app.models as _models  # Force import of models to populate metadata, use alias to avoid 'app' name collision

from sqlalchemy.pool import StaticPool

# Use SQLite in-memory for fast testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Creates a fresh database for each test function.
    """
    # Debug: Check if tables are registered
    print("Registered tables:", Base.metadata.tables.keys())
    
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient with overridden database dependency.
    """
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
    """
    Mocks the GeminiClient to avoid real API calls.
    """
    original_complete = gemini_client.complete
    mock = MagicMock()
    gemini_client.complete = mock
    
    yield mock
    
    # Restore original method
    gemini_client.complete = original_complete
