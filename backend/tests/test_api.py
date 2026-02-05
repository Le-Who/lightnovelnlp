def test_create_project(client):
    response = client.post("/projects/", json={
        "name": "Test Project",
        "genre": "fantasy"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["genre"] == "fantasy"
    assert "id" in data

def test_list_projects(client):
    # Create a project first
    client.post("/projects/", json={"name": "P1", "genre": "fantasy"})
    client.post("/projects/", json={"name": "P2", "genre": "scifi"})
    
    response = client.get("/projects/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "P2" # Ordered by created_at desc

def test_security_headers(client):
    response = client.get("/")
    assert response.status_code == 200
    headers = response.headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-XSS-Protection"] == "1; mode=block"
    assert "Strict-Transport-Security" in headers
    assert "Content-Security-Policy" in headers
