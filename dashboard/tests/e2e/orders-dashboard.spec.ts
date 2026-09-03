import { test, expect } from '@playwright/test';

test('Dashboard carga la lista de pedidos', async ({ page }) => {
  await page.goto('/');

  await expect(
    page.getByRole('heading', { name: 'Pedidos', exact: true })
  ).toBeVisible();

  await expect(page.locator('body')).toContainText(/pedidos/i);
});