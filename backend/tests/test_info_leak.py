from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_info_endpoint_removed():
    response = client.get("/info")
    assert response.status_code == 404

def test_api_usage_endpoint_removed():
    response = client.get("/glossary/api-usage")
    assert response.status_code == 404

def test_cache_stats_endpoint_removed():
    response = client.get("/glossary/cache-stats")
    assert response.status_code == 404
