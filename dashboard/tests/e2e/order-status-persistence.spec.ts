import { test, expect } from '@playwright/test';

import {
  API_BASE_URL,
  authenticateDashboardPage,
  getTenantHeaders,
} from './support/auth';

test(
  'Dashboard conserva el estado del pedido despues de recargar',
  async ({ page, request }) => {
    let orderId: number | null = null;
    let accessToken: string | null = null;

    try {
      accessToken = await authenticateDashboardPage(
        page,
        request,
      );

      const createResponse = await request.post(
        `${API_BASE_URL}/orders/`,
        {
          headers: {
            'X-Tenant': 'lpdb',
          },
          data: {
            customer_name:
              'E2E Dashboard Persistence Test',
            location_id: 1,
            items: [
              {
                product: 'PERRO DEL BARRIO',
                quantity: 1,
                modifications: [],
                combo_requested: false,
              },
            ],
          },
        },
      );

      expect(createResponse.ok()).toBeTruthy();

      const createdOrder = await createResponse.json();

      orderId = createdOrder.order.id;

      expect(orderId).toBeGreaterThan(0);

      await page.goto('/pedidos');

      await expect(
        page.getByRole('heading', {
          name: 'Pedidos',
          exact: true,
        }),
      ).toBeVisible();

      const order = page
        .locator('tbody tr[role="button"]')
        .filter({
          hasText: `#${orderId}`,
        });

      await expect(order).toBeVisible();

      await expect(
        order.getByText('Nuevo', {
          exact: true,
        }),
      ).toBeVisible();

      await order.click();

      await expect(
        page.getByRole('heading', {
          name: `Pedido #${orderId}`,
          exact: true,
        }),
      ).toBeVisible();

      await page
        .getByRole('button', {
          name: 'Confirmar pedido',
        })
        .click();

      const detail = page
        .locator('aside')
        .filter({
          has: page.getByRole('heading', {
            name: `Pedido #${orderId}`,
            exact: true,
          }),
        });

      await expect(
        detail.getByText('Confirmado', {
          exact: true,
        }),
      ).toBeVisible();

      await page.reload();

      await expect(
        page.getByRole('heading', {
          name: 'Pedidos',
          exact: true,
        }),
      ).toBeVisible();

      const reloadedOrder = page
        .locator('tbody tr[role="button"]')
        .filter({
          hasText: `#${orderId}`,
        });

      await expect(reloadedOrder).toBeVisible();

      await reloadedOrder.click();

      await expect(
        page.getByRole('heading', {
          name: `Pedido #${orderId}`,
          exact: true,
        }),
      ).toBeVisible();

      const reloadedDetail = page
        .locator('aside')
        .filter({
          has: page.getByRole('heading', {
            name: `Pedido #${orderId}`,
            exact: true,
          }),
        });

      await expect(
        reloadedDetail.getByText('Confirmado', {
          exact: true,
        }),
      ).toBeVisible();

      await expect(
        reloadedDetail.getByRole('button', {
          name: 'Confirmar pedido',
        }),
      ).toHaveCount(0);
    } finally {
      if (orderId !== null && accessToken !== null) {
        const deleteResponse = await request.delete(
          `${API_BASE_URL}/orders/${orderId}`,
          {
            headers: getTenantHeaders(accessToken),
          },
        );

        expect(deleteResponse.status()).toBe(204);
      }
    }
  },
);
