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
