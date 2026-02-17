from fastapi.testclient import TestClient
import pytest
from app.main import app

# Create a TestClient instance
client = TestClient(app)

def test_info_endpoint_removed():
    """Verify that the /info endpoint returns 404 Not Found."""
    response = client.get("/info")
    assert response.status_code == 404, "The /info endpoint should be removed"

def test_api_usage_endpoint_removed():
    """Verify that the /glossary/api-usage endpoint returns 404 Not Found."""
    response = client.get("/glossary/api-usage")
    assert response.status_code == 404, "The /glossary/api-usage endpoint should be removed"

def test_cache_stats_endpoint_removed():
    """Verify that the /glossary/cache-stats endpoint returns 404 Not Found."""
    response = client.get("/glossary/cache-stats")
    assert response.status_code == 404, "The /glossary/cache-stats endpoint should be removed"
