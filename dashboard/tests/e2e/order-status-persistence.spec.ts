import { test, expect } from '@playwright/test';

test('Dashboard conserva el estado del pedido después de recargar', async ({
  page,
  request,
}) => {
  const apiBaseUrl = 'http://127.0.0.1:8000';

  let orderId: number | null = null;

  try {
    // ========================================================
    // 1. CREAR PEDIDO DE PRUEBA
    // ========================================================

    const createResponse = await request.post(
      `${apiBaseUrl}/orders/`,
      {
        headers: {
          'X-Tenant': 'lpdb',
        },
        data: {
          customer_name: 'E2E Dashboard Persistence Test',
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

    // ========================================================
    // 2. ABRIR DASHBOARD
    // ========================================================

    await page.goto('/');

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

    // ========================================================
    // 3. ABRIR DETALLE
    // ========================================================

    await order.click();

    await expect(
      page.getByRole('heading', {
        name: `Pedido #${orderId}`,
        exact: true,
      }),
    ).toBeVisible();

    // ========================================================
    // 4. CONFIRMAR PEDIDO
    // ========================================================

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

    // ========================================================
    // 5. RECARGAR LA PÁGINA
    // ========================================================

    await page.reload();

    await expect(
      page.getByRole('heading', {
        name: 'Pedidos',
        exact: true,
      }),
    ).toBeVisible();

    // ========================================================
    // 6. VOLVER A ABRIR EL MISMO PEDIDO
    // ========================================================

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

    // ========================================================
    // 7. VERIFICAR PERSISTENCIA REAL DEL ESTADO
    // ========================================================

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
    // ========================================================
    // 8. LIMPIEZA
    // ========================================================

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