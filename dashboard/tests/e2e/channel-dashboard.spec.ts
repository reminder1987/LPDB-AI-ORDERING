import { test, expect } from '@playwright/test';
import { execFileSync } from 'child_process';
import { createHmac } from 'node:crypto';

import {
  API_BASE_URL,
  authenticateDashboardPage,
  getTenantHeaders,
} from './support/auth';

function buildWebhookSignature(
  payload: string,
  secret: string,
): string {
  const digest = createHmac('sha256', secret)
    .update(payload, 'utf8')
    .digest('hex');

  return `sha256=${digest}`;
}

test(
  'Canal crea pedido y Dashboard lo recibe y confirma',
  async ({ page, request }) => {
    const uniqueId = Date.now();

    const businessExternalId =
      `e2e-dashboard-business-${uniqueId}`;

    const customerExternalId =
      `e2e-dashboard-customer-${uniqueId}`;

    const sessionId =
      `e2e-dashboard-session-${uniqueId}`;

    let orderId: number | null = null;
    let accessToken: string | null = null;
    let webhookSecret: string | null = null;

    const projectRoot = process.cwd().endsWith('dashboard')
      ? '..'
      : '.';

    async function sendChannelMessage(
      message: string,
    ) {
      if (!webhookSecret) {
        throw new Error(
          'Webhook secret was not initialized.',
        );
      }

      const payload = {
        provider: 'meta',
        business_external_id: businessExternalId,
        external_id: customerExternalId,
        session_id: sessionId,
        customer_name: 'E2E Channel Dashboard Test',
        message,
        phone: '3050000099',
        email: 'e2e-channel-dashboard@example.com',
      };

      const rawBody = JSON.stringify(payload);

      return request.post(
        `${API_BASE_URL}/webhooks/whatsapp`,
        {
          headers: {
            'Content-Type': 'application/json',
            'X-Webhook-Signature':
              buildWebhookSignature(
                rawBody,
                webhookSecret,
              ),
          },
          data: rawBody,
        },
      );
    }

    try {
      accessToken = await authenticateDashboardPage(
        page,
        request,
      );

      const secretOutput = execFileSync(
        'python',
        [
          '-c',
          `
from app.services.channel_integration_service import ChannelIntegrationService

service = ChannelIntegrationService()

integration = service.create_integration(
    tenant_id=1,
    channel="whatsapp",
    provider="meta",
    external_id="${businessExternalId}",
)

print(integration.webhook_secret)
`,
        ],
        {
          cwd: projectRoot,
          encoding: 'utf8',
        },
      );

      webhookSecret = secretOutput.trim();

      expect(webhookSecret.length).toBeGreaterThan(0);

      const channelResponse =
        await sendChannelMessage(
          'Quiero un perro del barrio',
        );

      expect(channelResponse.ok()).toBeTruthy();

      const channelResult =
        await channelResponse.json();

      expect(
        channelResult.customer_id,
      ).toBeGreaterThan(0);

      expect(
        channelResult.status,
      ).toBe('needs_input');

      const locationResponse =
        await sendChannelMessage('Dirty Rabbit');

      expect(locationResponse.ok()).toBeTruthy();

      const comboResponse =
        await sendChannelMessage('NO');

      expect(comboResponse.ok()).toBeTruthy();

      const confirmationResponse =
        await sendChannelMessage('SI');

      expect(
        confirmationResponse.ok(),
      ).toBeTruthy();

      const confirmationResult =
        await confirmationResponse.json();

      expect(
        confirmationResult.status,
      ).toBe('ready');

      expect(
        confirmationResult.order,
      ).toBeDefined();

      expect(
        confirmationResult.order.id,
      ).toBeGreaterThan(0);

      orderId = confirmationResult.order.id;

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
    } finally {
      if (
        orderId !== null &&
        accessToken !== null
      ) {
        const deleteResponse =
          await request.delete(
            `${API_BASE_URL}/orders/${orderId}`,
            {
              headers:
                getTenantHeaders(accessToken),
            },
          );

        expect(
          deleteResponse.status(),
        ).toBe(204);
      }

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
  },
);