import { test, expect } from '@playwright/test';

test('Dashboard permite abrir el detalle de un pedido', async ({ page }) => {
  await page.goto('/');

  await expect(
    page.getByRole('heading', { name: 'Pedidos', exact: true })
  ).toBeVisible();

  const firstOrder = page.locator('tbody tr[role="button"]').first();

  await expect(firstOrder).toBeVisible();

  await firstOrder.click();

  await expect(
    page.getByRole('heading', { name: /^Pedido #\d+$/ })
  ).toBeVisible();

  await expect(page.getByText('Detalle', { exact: true })).toBeVisible();
});