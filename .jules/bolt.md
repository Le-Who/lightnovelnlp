## 2025-05-18 - [Schema Drift & Missing Indexes]
**Learning:** Found that `BatchJobItem` index was present in `000_initial.py` migration but missing in SQLAlchemy model definition. This caused `Base.metadata.create_all()` (used in tests/repro) to create unindexed tables, leading to poor test performance, while production (migrated) DBs were fine.
**Action:** Always check both Model definitions AND Migration history when diagnosing missing indexes. Fix Model definitions to match Schema to ensure tests reflect production performance.
## 2025-05-22 - [Schema Drift & Missing Indexes]
**Learning:** `000_initial.py` migration created indexes (e.g., `BatchJobItem.batch_job_id`) that were missing from SQLAlchemy models. This caused drift where the code didn't reflect the DB state. Also, `TermRelationship` FKs were completely unindexed, which is a major bottleneck for glossaries.
**Action:** When optimizing models, always cross-reference `alembic/versions/000_initial.py` (or relevant migrations) with the model definitions. Don't assume `autogenerate` will catch everything if you can't run it against a live prod-like DB. Manually verifying FK indexes is a high-yield manual check.
## 2025-05-24 - [Over-fetching Large Text Columns]
**Learning:** `TranslationService._get_project_summary` was fetching ALL chapters (including heavy `original_text` and `translated_text` columns) and then slicing in Python to get the first 5. This caused a 128x performance penalty (0.45s vs 0.0035s) due to IO and object construction overhead.
**Action:** Always use `.limit()` in SQL queries when only a subset is needed. Use `load_only()` or `defer()` to exclude large TEXT/BLOB columns when only metadata is required.
## 2025-05-25 - [Removed Unused Heavy Dependency]
**Learning:** The `spacy` library (and its models) was being downloaded in the Dockerfile and imported in `term_extractor.py` but never actually used in the execution path (which used Gemini and Regex). Removing it saved significant build time, image size (~100MB+), and runtime memory overhead.
**Action:** Periodically audit `requirements.txt` and `imports` to identify large unused libraries, especially those that download external assets (models) during build.
