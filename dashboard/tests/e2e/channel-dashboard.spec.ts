import { test, expect } from '@playwright/test';
import { execFileSync } from 'child_process';

test('Canal crea pedido y Dashboard lo recibe y confirma', async ({
  page,
  request,
}) => {
  const apiBaseUrl = 'http://127.0.0.1:8000';

  const uniqueId = Date.now();

  const businessExternalId =
    `e2e-dashboard-business-${uniqueId}`;

  const customerExternalId =
    `e2e-dashboard-customer-${uniqueId}`;

  const sessionId =
    `e2e-dashboard-session-${uniqueId}`;

  let orderId: number | null = null;

  const projectRoot = process.cwd().endsWith('dashboard')
    ? '..'
    : '.';

  try {
    // ========================================================
    // 1. CREAR INTEGRACIÓN DE CANAL PARA LA PRUEBA
    // ========================================================

    execFileSync(
      'python',
      [
        '-c',
        `
from app.services.channel_integration_service import ChannelIntegrationService

service = ChannelIntegrationService()

service.create_integration(
    tenant_id=1,
    channel="whatsapp",
    provider="meta",
    external_id="${businessExternalId}",
)
`,
      ],
      {
        cwd: projectRoot,
        stdio: 'inherit',
      },
    );

    // ========================================================
    // 2. WHATSAPP → PRIMER MENSAJE
    // ========================================================

    const channelResponse = await request.post(
      `${apiBaseUrl}/webhooks/whatsapp`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        data: {
          provider: 'meta',
          business_external_id: businessExternalId,
          external_id: customerExternalId,
          session_id: sessionId,
          customer_name: 'E2E Channel Dashboard Test',
          message: 'Quiero un perro del barrio',
          phone: '3050000099',
          email: 'e2e-channel-dashboard@example.com',
        },
      },
    );

    expect(channelResponse.ok()).toBeTruthy();

    const channelResult = await channelResponse.json();

    expect(channelResult.customer_id).toBeGreaterThan(0);
    expect(channelResult.status).toBe('needs_input');

    // ========================================================
    // 3. WHATSAPP → SEDE
    // ========================================================

    const locationResponse = await request.post(
      `${apiBaseUrl}/webhooks/whatsapp`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        data: {
          provider: 'meta',
          business_external_id: businessExternalId,
          external_id: customerExternalId,
          session_id: sessionId,
          customer_name: 'E2E Channel Dashboard Test',
          message: 'Dirty Rabbit',
          phone: '3050000099',
          email: 'e2e-channel-dashboard@example.com',
        },
      },
    );

    expect(locationResponse.ok()).toBeTruthy();

    // ========================================================
    // 4. WHATSAPP → NO COMBO
    // ========================================================

    const comboResponse = await request.post(
      `${apiBaseUrl}/webhooks/whatsapp`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        data: {
          provider: 'meta',
          business_external_id: businessExternalId,
          external_id: customerExternalId,
          session_id: sessionId,
          customer_name: 'E2E Channel Dashboard Test',
          message: 'NO',
          phone: '3050000099',
          email: 'e2e-channel-dashboard@example.com',
        },
      },
    );

    expect(comboResponse.ok()).toBeTruthy();

    // ========================================================
    // 5. WHATSAPP → CONFIRMACIÓN DEL PEDIDO
    // ========================================================

    const confirmationResponse = await request.post(
      `${apiBaseUrl}/webhooks/whatsapp`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        data: {
          provider: 'meta',
          business_external_id: businessExternalId,
          external_id: customerExternalId,
          session_id: sessionId,
          customer_name: 'E2E Channel Dashboard Test',
          message: 'SI',
          phone: '3050000099',
          email: 'e2e-channel-dashboard@example.com',
        },
      },
    );

    expect(confirmationResponse.ok()).toBeTruthy();

    const confirmationResult =
      await confirmationResponse.json();

    // ========================================================
    // 6. VALIDAR PEDIDO DEVUELTO POR EL CANAL
    //
    // WhatsAppAdapter aplana response.data mediante:
    //
    //     result.update(response.data)
    //
    // Por eso "order" está directamente en la respuesta.
    // ========================================================

    expect(confirmationResult.status).toBe('ready');
    expect(confirmationResult.order).toBeDefined();
    expect(confirmationResult.order.id).toBeGreaterThan(0);

    orderId = confirmationResult.order.id;

    // ========================================================
    // 7. DASHBOARD → VERIFICAR QUE RECIBE EL MISMO PEDIDO
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
    // 8. DASHBOARD → ABRIR DETALLE
    // ========================================================

    await order.click();

    await expect(
      page.getByRole('heading', {
        name: `Pedido #${orderId}`,
        exact: true,
      }),
    ).toBeVisible();

    // ========================================================
    // 9. DASHBOARD → CONFIRMAR PEDIDO
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
  } finally {
    // ========================================================
    // 10. LIMPIEZA DEL PEDIDO
    // ========================================================

    if (orderId !== null) {
      const deleteResponse =
        await request.delete(
          `${apiBaseUrl}/orders/${orderId}`,
          {
            headers: {
              'X-Tenant': 'lpdb',
            },
          },
        );

      expect(deleteResponse.status()).toBe(204);
    }

    // ========================================================
    // 11. LIMPIEZA DE LA INTEGRACIÓN DE PRUEBA
    // ========================================================

    execFileSync(
      'python',
      [
        '-c',
        `
from app.core.database import SessionLocal
from app.models.channel_integration_db import ChannelIntegrationDB
from sqlalchemy import delete

db = SessionLocal()

try:
    db.execute(
        delete(ChannelIntegrationDB).where(
            ChannelIntegrationDB.external_id == "${businessExternalId}"
        )
    )

    db.commit()

finally:
    db.close()
`,
      ],
      {
        cwd: projectRoot,
        stdio: 'inherit',
      },
    );
  }
});