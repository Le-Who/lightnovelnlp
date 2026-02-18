import pytest
from sqlalchemy import inspect
from app.models.glossary import GlossaryTerm

def test_glossary_terms_indexes(db):
    """
    Verifies that the glossary_terms table has the expected indexes.
    """
    inspector = inspect(db.bind)
    indexes = inspector.get_indexes("glossary_terms")

    index_names = [idx['name'] for idx in indexes]

    # Check for the new indexes
    assert "ix_glossary_terms_project_status_created" in index_names, "Missing index on (project_id, status, created_at)"
    assert "ix_glossary_terms_project_frequency" in index_names, "Missing index on (project_id, frequency)"

    # Check existing index
    assert "ix_glossary_terms_project_id" in index_names, "Missing index on project_id"

    # Verify column order for composite indexes
    status_idx = next(idx for idx in indexes if idx['name'] == "ix_glossary_terms_project_status_created")
    assert status_idx['column_names'] == ['project_id', 'status', 'created_at']

    freq_idx = next(idx for idx in indexes if idx['name'] == "ix_glossary_terms_project_frequency")
    assert freq_idx['column_names'] == ['project_id', 'frequency']
