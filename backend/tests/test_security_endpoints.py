from fastapi.testclient import TestClient

def test_sensitive_endpoints_removed(client: TestClient):
    """
    Verify that sensitive debug/info endpoints have been removed and return 404.
    """
    # Test /info endpoint
    response = client.get("/info")
    assert response.status_code == 404, f"Expected 404 for /info, but got {response.status_code}"

    # Test /glossary/api-usage endpoint
    response = client.get("/glossary/api-usage")
    assert response.status_code == 404, f"Expected 404 for /glossary/api-usage, but got {response.status_code}"

    # Test /glossary/cache-stats endpoint
    response = client.get("/glossary/cache-stats")
    assert response.status_code == 404, f"Expected 404 for /glossary/cache-stats, but got {response.status_code}"
