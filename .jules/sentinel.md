## 2026-02-04 - ReDoS in Regex Input
**Vulnerability:** User-supplied regex pattern in `upload_chapters_from_file` was passed directly to `re.compile` without validation.
**Learning:** Even "internal" tools can be DoS vectors if they accept complex inputs like regexes. Python's `re` module is vulnerable to catastrophic backtracking.
**Prevention:** Validate input length for regex fields. Always verify inputs passed to regex engines.
