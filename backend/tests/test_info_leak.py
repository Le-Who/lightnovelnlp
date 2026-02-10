from fastapi.testclient import TestClient

def test_info_endpoint_removed(client: TestClient):
    """
    Verify that the /info endpoint which leaked environment configuration is removed.
    """
    response = client.get("/info")
    assert response.status_code == 404, "Vulnerability: /info endpoint is exposed"

def test_api_usage_endpoint_removed(client: TestClient):
    """
    Verify that the /glossary/api-usage endpoint which leaked API stats is removed.
    """
    response = client.get("/glossary/api-usage")
    assert response.status_code == 404, "Vulnerability: /glossary/api-usage endpoint is exposed"

def test_cache_stats_endpoint_removed(client: TestClient):
    """
    Verify that the /glossary/cache-stats endpoint which leaked cache status is removed.
    """
    response = client.get("/glossary/cache-stats")
    assert response.status_code == 404, "Vulnerability: /glossary/cache-stats endpoint is exposed"
