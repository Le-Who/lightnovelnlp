## 2026-02-07 - [ReDoS in User-Supplied Regex]
**Vulnerability:** User-provided regex patterns in `upload_chapters_from_file` allowed ReDoS attacks, crashing the server.
**Learning:** Python's `re` module lacks timeouts, making it unsafe for user input.
**Prevention:** Use `safe_finditer` from `backend/app/core/regex_utils.py` which isolates regex execution in a separate process with a strict timeout.
