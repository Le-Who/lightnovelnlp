## 2025-05-21 - [ReDoS Protection]
**Vulnerability:** Regular Expression Denial of Service (ReDoS) via user-supplied regex in chapter extraction.
**Learning:** Python's standard `re` module does not support timeouts. Running regex in the main process can block the event loop indefinitely if a malicious pattern is provided.
**Prevention:** Use `safe_finditer` from `backend/app/core/regex_utils.py` which executes regex in a separate process with a strict timeout.
