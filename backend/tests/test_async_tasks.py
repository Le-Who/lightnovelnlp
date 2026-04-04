import pytest
from unittest.mock import MagicMock, patch

# Celery → pydantic.v1 → incompatible with Python 3.14 (local env).
# This guard prevents a CollectionError; tests run normally on Python 3.12 (production).
try:
    from app.tasks.nlp_tasks import translate_chapter_task
    from app.services.translation_service import TranslationService
    _CELERY_AVAILABLE = True
except Exception as _e:
    _CELERY_AVAILABLE = False

if not _CELERY_AVAILABLE:
    pytest.skip("Celery/Pydantic v1 unavailable on this Python version", allow_module_level=True)

@patch("app.tasks.nlp_tasks.SessionLocal")
@patch("app.tasks.nlp_tasks.TranslationService.translate_chapter")
def test_translate_chapter_task(mock_translate, mock_session):
    # Setup
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    
    mock_translate.return_value = {"status": "success"}
    
    # Execute (calling task directly as a function, bypassing broker)
    result = translate_chapter_task(1)
    
    # Verify
    mock_translate.assert_called_once_with(mock_db, 1)
    assert result == {"status": "success"}
    mock_db.close.assert_called_once()
    
    print("Async task test passed")

if __name__ == "__main__":
    test_translate_chapter_task()
