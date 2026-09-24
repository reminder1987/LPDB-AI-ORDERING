import { test, expect } from '@playwright/test';

import {
  authenticateDashboardPage,
} from './support/auth';

test(
  'Dashboard carga la lista de pedidos',
  async ({ page, request }) => {
    await authenticateDashboardPage(page, request);

    await page.goto('/pedidos');

    await expect(
      page.getByRole('heading', {
        name: 'Pedidos',
        exact: true,
      }),
    ).toBeVisible();

    await expect(
      page.locator('tbody tr[role="button"]').first(),
    ).toBeVisible();

    await expect(
      page.locator('body'),
    ).toContainText(/pedidos/i);
  },
);
