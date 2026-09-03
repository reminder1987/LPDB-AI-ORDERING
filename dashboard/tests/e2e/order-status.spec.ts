import { test, expect } from '@playwright/test';

test('Dashboard permite confirmar un pedido', async ({ page, request }) => {
  const apiBaseUrl = 'http://127.0.0.1:8000';

  let orderId: number | null = null;

  try {
    const createResponse = await request.post(`${apiBaseUrl}/orders/`, {
      headers: {
        'X-Tenant': 'lpdb',
      },
      data: {
        customer_name: 'E2E Dashboard Status Test',
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
    });

    expect(createResponse.ok()).toBeTruthy();

    const createdOrder = await createResponse.json();

    orderId = createdOrder.order.id;

    expect(orderId).toBeGreaterThan(0);

    await page.goto('/');

    await expect(
      page.getByRole('heading', { name: 'Pedidos', exact: true })
    ).toBeVisible();

    const order = page.locator('tbody tr[role="button"]').filter({
      hasText: `#${orderId}`,
    });

    await expect(order).toBeVisible();

    await expect(
      order.getByText('Nuevo', { exact: true })
    ).toBeVisible();

    await order.click();

    const detail = page.locator('aside').filter({
      has: page.getByRole('heading', {
        name: `Pedido #${orderId}`,
        exact: true,
      }),
    });

    await expect(
      page.getByRole('heading', {
        name: `Pedido #${orderId}`,
        exact: true,
      })
    ).toBeVisible();

    await page.getByRole('button', {
      name: 'Confirmar pedido',
    }).click();

    await expect(
      detail.getByText('Confirmado', { exact: true })
    ).toBeVisible();
  } finally {
    if (orderId !== null) {
      const deleteResponse = await request.delete(
        `${apiBaseUrl}/orders/${orderId}`,
        {
          headers: {
            'X-Tenant': 'lpdb',
          },
        },
      );

      expect(deleteResponse.status()).toBe(204);
    }
  }
});