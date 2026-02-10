## 2024-05-22 - Semantic Theming with Tailwind v4
**Learning:** Tailwind v4 simplifies theming by allowing direct mapping of CSS variables in the CSS file using `@theme`. This removes the need for a complex `tailwind.config.js` for basic color tokenization. However, it requires careful refactoring of components to use semantic names (e.g., `bg-primary`) instead of hardcoded colors (e.g., `bg-slate-900`) to enable multi-theme support (Light, Dark, Neutral).
**Action:** When implementing themes, start by defining the semantic palette in CSS, then refactor components one by one. Use `Playwright` to visually verify theme switching, as unit tests might miss visual regressions or contrast issues.

## 2024-05-23 - Inconsistent Modal Implementation Pattern
**Learning:** This application frequently re-implements custom modals (e.g., `GlossaryEditor`, `ChapterManager`) instead of using the shared, accessible `Modal` component. These custom implementations consistently lack critical accessibility features like `role="dialog"`, `aria-modal="true"`, and `Escape` key handling.
**Action:** When encountering custom modals, prioritize refactoring to use the shared `Modal` component if possible. If visual customization requires a custom implementation, ensure it includes all ARIA attributes and keyboard interactions (Escape, focus trap) to match the shared component's accessibility standards.
