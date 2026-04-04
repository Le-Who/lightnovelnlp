import { http, HttpResponse } from 'msw';

/**
 * MSW default handlers — global happy-path stubs.
 *
 * Route prefix: /api/v1 — matches VITE_API_URL set in vite.config.js test.env.
 * Rule: specific paths (with more segments) come BEFORE generic /:id matchers
 * so that path-to-regexp first-match semantics give the right handler.
 */
export const handlers = [
  // ── Projects API ──────────────────────────────────────────────────────────

  http.get('*/api/v1/projects/', () => {
    return HttpResponse.json([
      { id: 1, name: 'Project Alpha', genre: 'scifi',    chapters_count: 5, created_at: new Date().toISOString() },
      { id: 2, name: 'Project Beta',  genre: 'fantasy',  chapters_count: 2, created_at: new Date().toISOString() },
    ]);
  }),

  http.post('*/api/v1/projects/', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: 3, name: body.name, genre: body.genre, chapters_count: 0, created_at: new Date().toISOString() });
  }),

  http.delete('*/api/v1/projects/:id', () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // ─────────────────────────────────────────────────────────────────────────
  // IMPORTANT: specific sub-resource paths BEFORE the generic /:id handler
  // ─────────────────────────────────────────────────────────────────────────

  http.get('*/api/v1/projects/:id/chapters', () => {
    return HttpResponse.json([
      { id: 10, title: 'Chapter 1', analysis_status: 'completed', translation_status: 'completed' },
    ]);
  }),

  http.post('*/api/v1/projects/:id/chapters', () => {
    return HttpResponse.json({ id: 11, title: 'New Chapter' });
  }),

  http.get('*/api/v1/projects/:id/glossary', () => {
    return HttpResponse.json([
      { id: 100, term: 'Sword', equivalent: 'Jian', type: 'item' },
    ]);
  }),

  // Generic project-by-id — must come AFTER sub-resource routes
  http.get('*/api/v1/projects/:id', () => {
    return HttpResponse.json({ id: 1, name: 'Test Project', genre: 'scifi', created_at: new Date().toISOString() });
  }),

  // ── Translation / AI Review API ───────────────────────────────────────────
  // specific sub-paths first
  http.get('*/api/v1/translation/chapters/:id/review', () => {
    return HttpResponse.json({
      review_available: true,
      review_text: JSON.stringify({
        score: 8,
        passed: true,
        violations: [{ term: 'Aura', expected: 'Qi', found: 'Aura', context: 'Used Aura here' }],
        style_notes: ['Use formal tone'],
      }),
    });
  }),

  http.post('*/api/v1/translation/chapters/:id/review', () => {
    return HttpResponse.json({ status: 'started' });
  }),

  http.post('*/api/v1/translation/chapters/:id/translate-with-review', () => {
    return HttpResponse.json({ status: 'corrected' });
  }),

  http.get('*/api/v1/translation/chapters/:id/relationships', () => {
    return HttpResponse.json([]);
  }),

  // Generic chapter-by-id — must come AFTER sub-resource routes
  http.get('*/api/v1/translation/chapters/:id', () => {
    return HttpResponse.json({
      id: 10,
      title: 'Chapter 1',
      original_text: 'Sword Master',
      translated_text: 'Мастер Меча',
    });
  }),
];
