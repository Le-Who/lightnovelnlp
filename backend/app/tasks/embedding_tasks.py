import logging
from typing import Optional

from app.core.celery_app import celery_app
from app.db import SessionLocal
from app.models.glossary import GlossaryTerm
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def generate_term_embedding_task(self, term_id: int) -> Optional[str]:
    """
    Background task to generate and store a vector embedding for a GlossaryTerm.
    Will fetch the term, generate the 768-dim L2-normalized embedding,
    and save it in embedding_vec.
    """
    logger.info(f"Starting embedding generation for term_id={term_id}")
    db = SessionLocal()
    try:
        term = db.get(GlossaryTerm, term_id)
        if not term:
            logger.warning(f"Term {term_id} not found, skipping embedding.")
            return "Term not found"

        if term.embedding_vec is not None:
            logger.info(f"Term {term_id} already has an embedding. Skipping.")
            return "Already generated"

        # Note: Embedding requires the translated_term as well if available
        # to maximize the semantic value, but `source_term` is the core.
        # We can embed both as context.
        text_to_embed = term.source_term
        if term.translated_term:
            text_to_embed += f" ({term.translated_term})"
        if term.context:
            text_to_embed += f" - {term.context}"

        logger.debug(f"Generating embedding for text: {text_to_embed}")
        vec = embedding_service.generate_embedding(text_to_embed)

        if vec is None:
            raise Exception("Failed to generate embedding (API returned None or crashed)")

        term.embedding_vec = vec
        db.commit()
        logger.info(f"Successfully saved embedding for term {term_id}")
        return "Success"

    except Exception as e:
        logger.error(f"Failed to generate embedding for term {term_id}: {e}", exc_info=True)
        db.rollback()
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries * 5)
    finally:
        db.close()
