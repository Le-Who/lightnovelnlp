"""
EmbeddingService — Generates and manages semantic embeddings via Gemini Embedding API.

Uses gemini-embedding-2-preview with output_dimensionality=768 (MRL-optimized).
All embeddings are L2-normalized before storage.
Uses pgvector for ANN search with HNSW index.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

# Dimensionality for MRL-optimized embeddings
EMBEDDING_DIM = 768


class EmbeddingService:
    """Generates and queries semantic embeddings using Gemini Embedding API."""

    def __init__(self):
        self.model_name = settings.GEMINI_MODEL_EMBEDDING
        self.api_keys = settings.GEMINI_API_KEYS
        self.dim = EMBEDDING_DIM
        # Similarity threshold (calibrated via scripts/calibrate_threshold.py)
        self.similarity_threshold = float(
            getattr(settings, "EMBEDDING_SIMILARITY_THRESHOLD", 0.75)
        )

    def generate_embedding(self, text: str) -> list[float] | None:
        """
        Generate a single embedding vector for text.
        Returns L2-normalized float list of length EMBEDDING_DIM, or None on failure.
        """
        if not text or not text.strip():
            return None

        for api_key in self.api_keys:
            try:
                client = genai.Client(api_key=api_key)
                result = client.models.embed_content(
                    model=self.model_name,
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=self.dim,
                    ),
                )
                if result and result.embeddings:
                    raw_vec = result.embeddings[0].values
                    return self._l2_normalize(raw_vec)
            except Exception as e:
                logger.warning(f"Embedding failed with key: {e}")
                continue

        logger.error("All keys failed for embedding generation")
        return None

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float] | None]:
        """
        Generate embeddings for a batch of texts.
        Returns list of L2-normalized vectors (or None for failures).
        """
        results: list[list[float] | None] = []
        for text in texts:
            results.append(self.generate_embedding(text))
        return results

    def vector_to_pgvector_literal(self, vec: list[float]) -> str:
        """Convert a Python list to pgvector literal string '[0.1,0.2,...]'."""
        return "[" + ",".join(f"{v:.8f}" for v in vec) + "]"

    def find_similar_terms(
        self,
        db_session: Any,
        query_embedding: list[float],
        project_id: int,
        limit: int = 10,
        threshold: float | None = None,
    ) -> list[dict]:
        """
        Find glossary terms with embeddings similar to query_embedding using pgvector.
        Uses cosine distance (<=> operator).

        Returns list of {term_id, source_term, translated_term, similarity}.
        """
        effective_threshold = threshold or self.similarity_threshold
        vec_literal = self.vector_to_pgvector_literal(query_embedding)

        sql = f"""
            SELECT
                id,
                source_term,
                translated_term,
                1 - (embedding_vec <=> '{vec_literal}'::vector) AS similarity
            FROM glossary_terms
            WHERE project_id = :project_id
              AND embedding_vec IS NOT NULL
              AND 1 - (embedding_vec <=> '{vec_literal}'::vector) >= :threshold
            ORDER BY embedding_vec <=> '{vec_literal}'::vector
            LIMIT :limit
        """

        from sqlalchemy import text

        result = db_session.execute(
            text(sql),
            {
                "project_id": project_id,
                "threshold": effective_threshold,
                "limit": limit,
            },
        )

        return [
            {
                "term_id": row[0],
                "source_term": row[1],
                "translated_term": row[2],
                "similarity": round(float(row[3]), 4),
            }
            for row in result
        ]

    @staticmethod
    def _l2_normalize(vec: list[float]) -> list[float]:
        """L2-normalize a vector. Required for cosine similarity with pgvector."""
        arr = np.array(vec, dtype=np.float32)
        norm = np.linalg.norm(arr)
        if norm == 0:
            return vec
        return (arr / norm).tolist()


# Global service instance
embedding_service = EmbeddingService()
