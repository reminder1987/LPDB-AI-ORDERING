import { test, expect } from '@playwright/test';

import {
  authenticateDashboardPage,
} from './support/auth';

test(
  'Dashboard permite abrir el detalle de un pedido',
  async ({ page, request }) => {
    await authenticateDashboardPage(page, request);

    await page.goto('/');

    await expect(
      page.getByRole('heading', {
        name: 'Pedidos',
        exact: true,
      }),
    ).toBeVisible();

    const firstOrder = page
      .locator('tbody tr[role="button"]')
      .first();

    await expect(firstOrder).toBeVisible();

    await firstOrder.click();

    await expect(
      page.getByRole('heading', {
        name: /^Pedido #\d+$/,
      }),
    ).toBeVisible();

    await expect(
      page.getByText('Detalle', {
        exact: true,
      }),
    ).toBeVisible();
  },
);