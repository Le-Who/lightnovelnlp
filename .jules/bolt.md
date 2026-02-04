## 2025-05-18 - [Schema Drift & Missing Indexes]
**Learning:** Found that `BatchJobItem` index was present in `000_initial.py` migration but missing in SQLAlchemy model definition. This caused `Base.metadata.create_all()` (used in tests/repro) to create unindexed tables, leading to poor test performance, while production (migrated) DBs were fine.
**Action:** Always check both Model definitions AND Migration history when diagnosing missing indexes. Fix Model definitions to match Schema to ensure tests reflect production performance.
