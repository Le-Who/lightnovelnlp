import { test, expect } from '@playwright/test';

test.describe('E2E: Translation Workflow (RAG loop)', () => {

  test('Creates a project and interacts with glossary terminology constraints', async ({ page }) => {
    // 1. Arrange: Go to dashboard
    await page.goto('http://localhost:3000');
    await expect(page).toHaveTitle(/Ranobe Translator/i);

    // 2. Act: Create project
    await page.getByPlaceholder(/Например/i).fill('E2E Sword God');
    await page.getByPlaceholder(/Выберите/i).fill('xianxia');
    await page.getByRole('button', { name: /Создать/i }).click();

    // Verify Project Created
    await expect(page.getByText('E2E Sword God')).toBeVisible();

    // 3. Navigate into Project Details
    await page.getByRole('link', { name: /E2E Sword God/i }).click();
    await expect(page).toHaveURL(/\/projects\/\d+/);

    // Expecting to see the Chapter form empty at first
    await expect(page.getByText(/Глоссарий/i)).toBeVisible();
    await expect(page.getByText(/Главы/i)).toBeVisible();
    
    // Note: E2E tests against real backend instances will need to assert 
    // real upload / processing results. This structure proves out the test shell
    // required for Playwright verification under the AAA pattern mapping.
  });
});
