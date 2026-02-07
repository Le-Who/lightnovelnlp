## 2024-05-22 - Semantic Theming with Tailwind v4
**Learning:** Tailwind v4 simplifies theming by allowing direct mapping of CSS variables in the CSS file using `@theme`. This removes the need for a complex `tailwind.config.js` for basic color tokenization. However, it requires careful refactoring of components to use semantic names (e.g., `bg-primary`) instead of hardcoded colors (e.g., `bg-slate-900`) to enable multi-theme support (Light, Dark, Neutral).
**Action:** When implementing themes, start by defining the semantic palette in CSS, then refactor components one by one. Use `Playwright` to visually verify theme switching, as unit tests might miss visual regressions or contrast issues.

## 2024-05-23 - Accessible File Inputs with Tailwind
**Learning:** Standard file inputs are often styled using `display: none` (`.hidden`), which removes them from the accessibility tree and keyboard navigation. Using `.sr-only` keeps the input focusable but visually hidden.
**Action:** When creating custom file inputs, use `.sr-only` on the input and `focus-within` utilities on the parent label to provide visible focus indicators for keyboard users.
