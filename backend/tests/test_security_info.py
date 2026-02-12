from fastapi.testclient import TestClient

def test_info_endpoint_removed(client: TestClient):
    """
    Verify that the /info endpoint is removed and returns 404.
    This is a security regression test to ensure sensitive configuration
    details are not exposed.
    """
    response = client.get("/info")
    assert response.status_code == 404
