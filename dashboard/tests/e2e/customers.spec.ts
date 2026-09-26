import {
  expect,
  test,
} from "@playwright/test";

import {
  API_BASE_URL,
  getOwnerAccessToken,
  getTenantHeaders,
} from "./support/auth";

test.describe("customers API", () => {
  test("lists customers for the authenticated tenant", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/customers`,
      {
        headers: getTenantHeaders(accessToken),
      },
    );

    expect(response.status()).toBe(200);

    const customers =
      (await response.json()) as unknown;

    expect(Array.isArray(customers)).toBe(true);
  });

  test("accepts supported customer filters", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/customers`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          search: "cliente",
          active: "true",
        },
      },
    );

    expect(response.status()).toBe(200);

    const customers =
      (await response.json()) as unknown;

    expect(Array.isArray(customers)).toBe(true);
  });

  test("accepts inactive customer filter", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/customers`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          active: "false",
        },
      },
    );

    expect(response.status()).toBe(200);

    const customers =
      (await response.json()) as unknown;

    expect(Array.isArray(customers)).toBe(true);
  });

  test("rejects an invalid active filter", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/customers`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          active: "invalid",
        },
      },
    );

    expect(response.status()).toBe(422);
  });

  test("returns 404 for an unknown customer", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/customers/2147483647`,
      {
        headers: getTenantHeaders(accessToken),
      },
    );

    expect(response.status()).toBe(404);
  });

  test("rejects a non-positive customer id", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/customers/0`,
      {
        headers: getTenantHeaders(accessToken),
      },
    );

    expect(response.status()).toBe(422);
  });
});