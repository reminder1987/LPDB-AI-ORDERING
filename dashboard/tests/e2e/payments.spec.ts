import {
  expect,
  test,
} from "@playwright/test";

import {
  API_BASE_URL,
  getOwnerAccessToken,
  getTenantHeaders,
} from "./support/auth";

test.describe("payments API", () => {
  test("lists payments for the authenticated tenant", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/payments`,
      {
        headers: getTenantHeaders(accessToken),
      },
    );

    expect(response.status()).toBe(200);

    const payments =
      (await response.json()) as unknown;

    expect(Array.isArray(payments)).toBe(true);
  });

  test("accepts supported payment filters", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/payments`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          status: "paid",
          provider: "toast",
        },
      },
    );

    expect(response.status()).toBe(200);

    const payments =
      (await response.json()) as unknown;

    expect(Array.isArray(payments)).toBe(true);
  });

  test("rejects an invalid payment status", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/payments`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          status: "invalid-status",
        },
      },
    );

    expect(response.status()).toBe(422);
  });

  test("rejects an empty provider filter", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/payments`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          provider: "   ",
        },
      },
    );

    expect(response.status()).toBe(422);
  });

  test("returns 404 for an unknown payment", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/payments/2147483647`,
      {
        headers: getTenantHeaders(accessToken),
      },
    );

    expect(response.status()).toBe(404);
  });
});