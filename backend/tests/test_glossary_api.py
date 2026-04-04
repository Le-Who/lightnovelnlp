import time
from app.models.glossary import GlossaryTerm, TermStatus


def test_glossary_terms_default_limit_enforced(client, db):
    # 1. Create a project
    project_response = client.post(
        "/projects/", json={"name": "Test Project", "genre": "fantasy"}
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # 2. Add 150 glossary terms
    for i in range(150):
        term = GlossaryTerm(
            project_id=project_id,
            source_term=f"Term {i}",
            translated_term=f"Translation {i}",
            category="other",
            status=TermStatus.APPROVED,
        )
        db.add(term)
    db.commit()

    # 3. Call GET /{project_id}/terms without limit
    start_time = time.time()
    response = client.get(f"/glossary/{project_id}/terms")
    end_time = time.time()

    assert response.status_code == 200
    data = response.json()

    # 4. Assert that only 50 terms are returned (default limit)
    print(
        f"\n[Optimization] Fetched {len(data)} terms in {end_time - start_time:.4f} seconds."
    )
    assert len(data) == 50, "Expected 50 terms to be returned by default."


def test_glossary_terms_with_limit_override(client, db):
    # 1. Create a project
    project_response = client.post(
        "/projects/", json={"name": "Test Project 2", "genre": "fantasy"}
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # 2. Add 150 glossary terms
    for i in range(150):
        term = GlossaryTerm(
            project_id=project_id,
            source_term=f"Term {i}",
            translated_term=f"Translation {i}",
            category="other",
            status=TermStatus.APPROVED,
        )
        db.add(term)
    db.commit()

    # 3. Call GET /{project_id}/terms with explicit limit
    start_time = time.time()
    response = client.get(f"/glossary/{project_id}/terms?limit=10")
    end_time = time.time()

    assert response.status_code == 200
    data = response.json()

    # 4. Assert that 10 terms are returned
    print(
        f"\n[Limit=10] Fetched {len(data)} terms in {end_time - start_time:.4f} seconds."
    )
    assert len(data) == 10, "Expected 10 terms to be returned with limit=10."


def test_glossary_terms_with_limit_large(client, db):
    # 1. Create a project
    project_response = client.post(
        "/projects/", json={"name": "Test Project 3", "genre": "fantasy"}
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # 2. Add 150 glossary terms
    for i in range(150):
        term = GlossaryTerm(
            project_id=project_id,
            source_term=f"Term {i}",
            translated_term=f"Translation {i}",
            category="other",
            status=TermStatus.APPROVED,
        )
        db.add(term)
    db.commit()

    # 3. Call GET /{project_id}/terms with explicit limit > 50
    start_time = time.time()
    response = client.get(f"/glossary/{project_id}/terms?limit=100")
    end_time = time.time()

    assert response.status_code == 200
    data = response.json()

    # 4. Assert that 100 terms are returned
    print(
        f"\n[Limit=100] Fetched {len(data)} terms in {end_time - start_time:.4f} seconds."
    )
    assert len(data) == 100, "Expected 100 terms to be returned with limit=100."
