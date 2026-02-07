## 2025-05-18 - [Schema Drift & Missing Indexes]
**Learning:** Found that `BatchJobItem` index was present in `000_initial.py` migration but missing in SQLAlchemy model definition. This caused `Base.metadata.create_all()` (used in tests/repro) to create unindexed tables, leading to poor test performance, while production (migrated) DBs were fine.
**Action:** Always check both Model definitions AND Migration history when diagnosing missing indexes. Fix Model definitions to match Schema to ensure tests reflect production performance.
## 2025-05-22 - [Schema Drift & Missing Indexes]
**Learning:** `000_initial.py` migration created indexes (e.g., `BatchJobItem.batch_job_id`) that were missing from SQLAlchemy models. This caused drift where the code didn't reflect the DB state. Also, `TermRelationship` FKs were completely unindexed, which is a major bottleneck for glossaries.
**Action:** When optimizing models, always cross-reference `alembic/versions/000_initial.py` (or relevant migrations) with the model definitions. Don't assume `autogenerate` will catch everything if you can't run it against a live prod-like DB. Manually verifying FK indexes is a high-yield manual check.
## 2025-05-24 - [Over-fetching Large Text Columns]
**Learning:** `TranslationService._get_project_summary` was fetching ALL chapters (including heavy `original_text` and `translated_text` columns) and then slicing in Python to get the first 5. This caused a 128x performance penalty (0.45s vs 0.0035s) due to IO and object construction overhead.
**Action:** Always use `.limit()` in SQL queries when only a subset is needed. Use `load_only()` or `defer()` to exclude large TEXT/BLOB columns when only metadata is required.
## 2025-05-25 - [spaCy Matcher for Lemmatized Frequency]
**Learning:** `TermExtractor` used regex `\bterm\b` which failed to count morphological variants (e.g. "cats" vs "cat"). Using `spaCy`'s `Matcher` with `LEMMA` attribute solves this efficiently.
**Action:** When precise linguistic matching is needed, prefer `spacy.matcher.Matcher` over regex. Optimize `nlp.pipe` by disabling unnecessary components (`ner`, `parser`) to keep performance high (O(TextLength) instead of O(N*TextLength) for regex).
## 2025-05-26 - [Avoid Heavy Object Instantiation for filtering]
**Learning:** `TranslationService` was fetching ALL `GlossaryTerm` objects (including relationships) and then filtering them in Python using `term.source_term.lower() in text`. This caused massive overhead (instantiating 1000s of SQLAlchemy models when only ~50 were relevant).
**Action:** Use a two-step query pattern: 1) Fetch lightweight tuples `(id, source_term)` from DB. 2) Filter in Python. 3) Fetch full objects by ID for matches. This reduces object instantiation overhead by >90% for sparse matches.
## 2025-05-27 - [selectinload fetches full objects]
**Learning:** `selectinload` on relationships eagerly loads the ENTIRE related object, including large TEXT columns (like `Chapter.original_text`). For `GlossaryTerm` which links to `Chapter`, this meant loading MBs of text just to display a chapter number.
**Action:** When using `selectinload` for relationships to heavy objects, ALWAYS chain `.load_only()` to fetch only necessary columns (e.g., `id`, `order`).
