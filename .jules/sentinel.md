## 2026-02-07 - ReDoS Protection in Python
**Vulnerability:** User-supplied regex pattern in `upload_chapters_from_file` could cause ReDoS (Regular Expression Denial of Service).
**Learning:** The standard Python `re` module lacks execution timeouts. To securely handle user-supplied regex patterns against large inputs, execution must be isolated in a separate process (using `multiprocessing`) to enforce a hard timeout.
**Prevention:** Use `app.core.regex_utils.safe_finditer` for any regex operation where the pattern or the text is user-controlled.
