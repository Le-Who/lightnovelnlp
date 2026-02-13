from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_info_endpoint_removed():
    """Verify that the /info endpoint is removed and returns 404."""
    response = client.get("/info")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}

def test_glossary_api_usage_removed():
    """Verify that the /glossary/api-usage endpoint is removed and returns 404."""
    response = client.get("/glossary/api-usage")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}

def test_glossary_cache_stats_removed():
    """Verify that the /glossary/cache-stats endpoint is removed and returns 404."""
    response = client.get("/glossary/cache-stats")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
