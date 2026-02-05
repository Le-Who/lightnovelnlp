## 2024-05-22 - Semantic Theming with Tailwind v4
**Learning:** Tailwind v4 simplifies theming by allowing direct mapping of CSS variables in the CSS file using `@theme`. This removes the need for a complex `tailwind.config.js` for basic color tokenization. However, it requires careful refactoring of components to use semantic names (e.g., `bg-primary`) instead of hardcoded colors (e.g., `bg-slate-900`) to enable multi-theme support (Light, Dark, Neutral).
**Action:** When implementing themes, start by defining the semantic palette in CSS, then refactor components one by one. Use `Playwright` to visually verify theme switching, as unit tests might miss visual regressions or contrast issues.

## 2024-05-23 - Form Label Association
**Learning:** The `Label` and `Input` components are decoupled in this design system. `Label` does not automatically associate with `Input` unless `htmlFor` and `id` are explicitly provided. This pattern is easily missed during development as visual proximity suggests association.
**Action:** Always verify `htmlFor` matches the `id` of the target input in forms. Consider adding `eslint-plugin-jsx-a11y` in the future to catch these automatically.
