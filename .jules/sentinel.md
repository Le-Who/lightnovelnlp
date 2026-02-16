## 2026-02-07 - [ReDoS in User-Supplied Regex]
**Vulnerability:** User-provided regex patterns in `upload_chapters_from_file` allowed ReDoS attacks, crashing the server.
**Learning:** Python's `re` module lacks timeouts, making it unsafe for user input.
**Prevention:** Use `safe_finditer` from `backend/app/core/regex_utils.py` which isolates regex execution in a separate process with a strict timeout.

## 2026-02-16 - [File Upload DoS]
**Vulnerability:** Unrestricted file upload size allowed users to crash the server by uploading extremely large files, causing Out-Of-Memory (OOM) errors when reading content into RAM.
**Learning:** `UploadFile.file.read()` loads the entire content into memory, even if the file is spooled on disk.
**Prevention:** Check file size using `seek(0, 2)` and `tell()` before reading content, and enforce a strict `MAX_UPLOAD_SIZE` limit in configuration.
