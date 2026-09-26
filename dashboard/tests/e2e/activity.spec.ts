import {
  expect,
  test,
} from "@playwright/test";

import {
  API_BASE_URL,
  getOwnerAccessToken,
  getTenantHeaders,
} from "./support/auth";

type ActivitySource =
  | "payment"
  | "incident"
  | "integration"
  | "webhook";

type ActivityResponse = {
  id: string;
  source: ActivitySource;
  event_type: string;
  title: string;
  description: string;
  occurred_at: string;
  entity_type: string;
  entity_id: string;
  provider: string | null;
  status: string | null;
  severity: string | null;
};

const supportedSources: ActivitySource[] = [
  "payment",
  "incident",
  "integration",
  "webhook",
];

function expectSafeActivityShape(
  activity: ActivityResponse,
) {
  expect(typeof activity.id).toBe("string");
  expect(
    supportedSources,
  ).toContain(activity.source);
  expect(typeof activity.event_type).toBe("string");
  expect(typeof activity.title).toBe("string");
  expect(typeof activity.description).toBe("string");
  expect(typeof activity.occurred_at).toBe("string");
  expect(typeof activity.entity_type).toBe("string");
  expect(typeof activity.entity_id).toBe("string");

  expect(activity).not.toHaveProperty("payload");
  expect(activity).not.toHaveProperty("configuration");
  expect(activity).not.toHaveProperty("credentials");
  expect(activity).not.toHaveProperty("credential_values");
  expect(activity).not.toHaveProperty("secrets");
}

test.describe("operational activity API", () => {
  test("lists activity for the authenticated tenant", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/activity`,
      {
        headers: getTenantHeaders(accessToken),
      },
    );

    expect(response.status()).toBe(200);

    const activities =
      (await response.json()) as ActivityResponse[];

    expect(Array.isArray(activities)).toBe(true);

    for (const activity of activities) {
      expectSafeActivityShape(activity);
    }
  });

  test("accepts every supported source filter", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const headers =
      getTenantHeaders(accessToken);

    for (const source of supportedSources) {
      const response = await request.get(
        `${API_BASE_URL}/activity`,
        {
          headers,
          params: {
            source,
          },
        },
      );

      expect(response.status()).toBe(200);

      const activities =
        (await response.json()) as ActivityResponse[];

      expect(Array.isArray(activities)).toBe(true);

      for (const activity of activities) {
        expect(activity.source).toBe(source);
        expectSafeActivityShape(activity);
      }
    }
  });

  test("accepts provider filter", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/activity`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          provider: "toast",
        },
      },
    );

    expect(response.status()).toBe(200);

    const activities =
      (await response.json()) as ActivityResponse[];

    expect(Array.isArray(activities)).toBe(true);

    for (const activity of activities) {
      expect(
        activity.provider?.toLowerCase(),
      ).toBe("toast");

      expectSafeActivityShape(activity);
    }
  });

  test("accepts source and provider filters together", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/activity`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          source: "webhook",
          provider: "toast",
        },
      },
    );

    expect(response.status()).toBe(200);

    const activities =
      (await response.json()) as ActivityResponse[];

    expect(Array.isArray(activities)).toBe(true);

    for (const activity of activities) {
      expect(activity.source).toBe("webhook");
      expect(
        activity.provider?.toLowerCase(),
      ).toBe("toast");

      expectSafeActivityShape(activity);
    }
  });

  test("rejects unsupported source filter", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/activity`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          source: "unknown",
        },
      },
    );

    expect(response.status()).toBe(422);
  });

  test("respects the requested limit", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/activity`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          limit: "1",
        },
      },
    );

    expect(response.status()).toBe(200);

    const activities =
      (await response.json()) as ActivityResponse[];

    expect(activities.length).toBeLessThanOrEqual(1);

    for (const activity of activities) {
      expectSafeActivityShape(activity);
    }
  });

  test("rejects an invalid limit", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/activity`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          limit: "0",
        },
      },
    );

    expect(response.status()).toBe(422);
  });

  test("does not expose sensitive operational source data", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/activity`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          limit: "250",
        },
      },
    );

    expect(response.status()).toBe(200);

    const activities =
      (await response.json()) as ActivityResponse[];

    const serialized =
      JSON.stringify(activities).toLowerCase();

    expect(serialized).not.toContain(
      "\"payload\":",
    );
    expect(serialized).not.toContain(
      "\"configuration\":",
    );
    expect(serialized).not.toContain(
      "\"credentials\":",
    );
    expect(serialized).not.toContain(
      "\"credential_values\":",
    );

    for (const activity of activities) {
      expectSafeActivityShape(activity);
    }
  });
});