## 2024-05-23 - ReDoS Vulnerability in Project Upload
**Vulnerability:** The `upload_chapters_from_file` endpoint in `backend/app/api/projects.py` accepts a user-controlled regex pattern (`chapter_pattern`) and compiles it using Python's `re` module without sanitization or timeout.
**Learning:** Using `re.compile` with untrusted input exposes the application to Regular Expression Denial of Service (ReDoS) attacks.
**Prevention:** Avoid user-defined regexes where possible. If necessary, use a safe regex engine like `google-re2` (via `google-re2` package) or strictly limit the pattern length and complexity (e.g., disallow nested quantifiers).
