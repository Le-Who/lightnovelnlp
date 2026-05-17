## 2024-05-23 - Glossary Table Accessibility
**Learning:** Icon-only buttons in data tables (like Edit/Delete rows) are unusable for screen readers without context. Relying on `title` is insufficient.
**Action:** Always add dynamic `aria-label` to row actions that includes the row's identifier (e.g., `aria-label="Delete term: [Term Name]"`), and verify with `getByRole` in tests.
