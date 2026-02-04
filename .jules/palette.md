## 2026-02-04 - Accessibility Gaps in Forms and Modals
**Learning:** Found critical accessibility issues where forms lacked `<label>` elements entirely, relying on placeholders. Modals were implemented as plain divs without ARIA roles or focus management, making them invisible to screen readers.
**Action:** Always verify form inputs have associated labels (visible or visually hidden) and ensure custom modals implementation includes `role="dialog"`, `aria-modal="true"`, and proper labeling.
