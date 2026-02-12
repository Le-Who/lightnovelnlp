from fastapi.testclient import TestClient

def test_info_endpoint_leak(client: TestClient):
    """
    Test that the /info endpoint is removed and returns 404.
    """
    response = client.get("/info")
    assert response.status_code == 404

def test_api_usage_leak(client: TestClient):
    """Test that the /glossary/api-usage endpoint is removed."""
    response = client.get("/glossary/api-usage")
    assert response.status_code == 404

def test_cache_stats_leak(client: TestClient):
    """Test that the /glossary/cache-stats endpoint is removed."""
    response = client.get("/glossary/cache-stats")
    assert response.status_code == 404
