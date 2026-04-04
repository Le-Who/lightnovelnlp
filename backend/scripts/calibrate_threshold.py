#!/usr/bin/env python3
"""
Calibrate embedding similarity threshold for a specific project.

Usage:
    python -m scripts.calibrate_threshold --project-id 1

This script:
1. Loads all approved glossary terms with embeddings for the project.
2. Computes pairwise cosine similarities.
3. Identifies optimal threshold via distribution analysis.
4. Prints recommended threshold and optionally updates ENV.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Calibrate embedding similarity threshold"
    )
    parser.add_argument(
        "--project-id", type=int, required=True, help="Project ID to analyze"
    )
    parser.add_argument(
        "--percentile",
        type=float,
        default=25.0,
        help="Percentile for threshold (default: 25th)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        # The first query was unused, removing it to pass lint F841

        # Collect terms that have embeddings (via raw SQL since embedding_vec is pgvector)
        from sqlalchemy import text

        rows = db.execute(
            text("""
                SELECT id, source_term, embedding_vec::text
                FROM glossary_terms
                WHERE project_id = :pid
                  AND status = 'approved'
                  AND embedding_vec IS NOT NULL
            """),
            {"pid": args.project_id},
        ).fetchall()

        if len(rows) < 5:
            logger.error(f"Need at least 5 terms with embeddings, found {len(rows)}.")
            logger.info("Run embedding generation first for this project.")
            return

        logger.info(
            f"Loaded {len(rows)} terms with embeddings from project {args.project_id}"
        )

        # Parse vectors
        vectors = {}
        for row in rows:
            vec_str = row[2]  # pgvector text format: "[0.1,0.2,...]"
            vec = np.array(
                [float(x) for x in vec_str.strip("[]").split(",")], dtype=np.float32
            )
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors[row[0]] = {"name": row[1], "vec": vec}

        # Compute pairwise cosine similarities
        ids = list(vectors.keys())
        n = len(ids)
        similarities = []

        for i in range(n):
            for j in range(i + 1, n):
                sim = float(np.dot(vectors[ids[i]]["vec"], vectors[ids[j]]["vec"]))
                similarities.append(sim)

        similarities = np.array(similarities)

        logger.info(f"\n=== Similarity Distribution ({len(similarities)} pairs) ===")
        logger.info(f"Min:    {similarities.min():.4f}")
        logger.info(f"P25:    {np.percentile(similarities, 25):.4f}")
        logger.info(f"Median: {np.median(similarities):.4f}")
        logger.info(f"P75:    {np.percentile(similarities, 75):.4f}")
        logger.info(f"Max:    {similarities.max():.4f}")
        logger.info(f"Mean:   {similarities.mean():.4f}")
        logger.info(f"Std:    {similarities.std():.4f}")

        threshold = float(np.percentile(similarities, args.percentile))
        logger.info("\n=== Recommendation ===")
        logger.info(f"Threshold (P{args.percentile}): {threshold:.4f}")
        logger.info(f"\nSet ENV: EMBEDDING_SIMILARITY_THRESHOLD={threshold:.4f}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
