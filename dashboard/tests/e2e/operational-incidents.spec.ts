import {
  expect,
  test,
} from '@playwright/test';

import {
  API_BASE_URL,
  getOwnerAccessToken,
  getTenantHeaders,
} from './support/auth';

test.describe('operational incidents API', () => {
  test('lists incidents for the authenticated tenant', async ({
    request,
  }) => {
    const accessToken = await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/operational/incidents`,
      {
        headers: getTenantHeaders(accessToken),
      },
    );

    expect(response.status()).toBe(200);

    const incidents = (await response.json()) as unknown;

    expect(Array.isArray(incidents)).toBe(true);
  });

  test('accepts supported incident filters', async ({
    request,
  }) => {
    const accessToken = await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/operational/incidents`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          status: 'open',
          severity: 'critical',
          category: 'provider',
        },
      },
    );

    expect(response.status()).toBe(200);

    const incidents = (await response.json()) as unknown;

    expect(Array.isArray(incidents)).toBe(true);
  });

  test('rejects an invalid incident filter', async ({
    request,
  }) => {
    const accessToken = await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/operational/incidents`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          status: 'invalid-status',
        },
      },
    );

    expect(response.status()).toBe(422);
  });
});