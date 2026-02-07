import pytest
from fastapi.testclient import TestClient

def test_create_glossary_term_valid(client: TestClient):
    # 1. Create a project
    project_response = client.post("/projects/", json={"name": "Test Project Valid"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # 2. Create valid term
    term_data = {
        "project_id": project_id,
        "source_term": "valid",
        "translated_term": "valid",
        "category": "other"
    }
    response = client.post("/glossary/terms", json=term_data)
    assert response.status_code == 201

def test_create_glossary_term_source_too_long(client: TestClient):
    # 1. Create a project
    project_response = client.post("/projects/", json={"name": "Test Project Source"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # 2. Attempt to create a term with source_term length 256
    long_term = "a" * 256
    term_data = {
        "project_id": project_id,
        "source_term": long_term,
        "translated_term": "valid",
        "category": "other"
    }
    response = client.post("/glossary/terms", json=term_data)

    # 3. Assert failure
    assert response.status_code == 422

def test_create_glossary_term_translated_too_long(client: TestClient):
    # 1. Create a project
    project_response = client.post("/projects/", json={"name": "Test Project Translated"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # 2. Attempt to create a term with translated_term length 256
    long_term = "a" * 256
    term_data = {
        "project_id": project_id,
        "source_term": "valid",
        "translated_term": long_term,
        "category": "other"
    }
    response = client.post("/glossary/terms", json=term_data)

    # 3. Assert failure
    assert response.status_code == 422

def test_create_glossary_term_category_too_long(client: TestClient):
    # 1. Create a project
    project_response = client.post("/projects/", json={"name": "Test Project Category"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # 2. Attempt to create a term with category length 51
    long_cat = "a" * 51
    term_data = {
        "project_id": project_id,
        "source_term": "valid",
        "translated_term": "valid",
        "category": long_cat
    }
    response = client.post("/glossary/terms", json=term_data)

    # 3. Assert failure
    assert response.status_code == 422
