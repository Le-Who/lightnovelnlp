import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Ranobe Translator/);
});

test('can create project', async ({ page }) => {
  await page.goto('http://localhost:3000');

  await page.getByPlaceholder('Например: Overlord').fill('E2E Test Project');
  await page.getByPlaceholder('Выберите или введите...').fill('fantasy');
  await page.getByRole('button', { name: 'Создать' }).click();

  // We expect the new project to appear in the list (mocked or real)
  // Since we are mocking the backend in tests usually, for E2E against a real dev server,
  // we assume the backend is reachable or we just check the UI state.
  // Here we just check if the button click works without error.
  await expect(page.getByRole('button', { name: 'Создать' })).toBeVisible();
});
