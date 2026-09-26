import {
  expect,
  test,
} from "@playwright/test";

import {
  API_BASE_URL,
  getOwnerAccessToken,
  getTenantHeaders,
} from "./support/auth";

type IntegrationResponse = {
  id: number;
  provider: string;
  integration_type: string;
  external_id: string | null;
  active: boolean;
  configuration: Record<string, unknown>;
  credential_names: string[];
  credentials_configured: boolean;
  created_at: string;
  updated_at: string;
};

function expectSafeIntegrationShape(
  integration: IntegrationResponse,
) {
  expect(typeof integration.id).toBe("number");
  expect(typeof integration.provider).toBe("string");
  expect(
    typeof integration.integration_type,
  ).toBe("string");
  expect(typeof integration.active).toBe("boolean");

  expect(
    Array.isArray(integration.credential_names),
  ).toBe(true);

  expect(
    typeof integration.credentials_configured,
  ).toBe("boolean");

  expect(integration).not.toHaveProperty(
    "credentials",
  );
  expect(integration).not.toHaveProperty(
    "credential_values",
  );
  expect(integration).not.toHaveProperty(
    "secrets",
  );
}

test.describe("integrations API", () => {
  test("lists integrations for the authenticated tenant", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/integrations`,
      {
        headers: getTenantHeaders(accessToken),
      },
    );

    expect(response.status()).toBe(200);

    const integrations =
      (await response.json()) as IntegrationResponse[];

    expect(Array.isArray(integrations)).toBe(true);

    for (const integration of integrations) {
      expectSafeIntegrationShape(integration);
    }
  });

  test("accepts supported integration filters", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/integrations`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          provider: "toast",
          active: "true",
        },
      },
    );

    expect(response.status()).toBe(200);

    const integrations =
      (await response.json()) as IntegrationResponse[];

    expect(Array.isArray(integrations)).toBe(true);

    for (const integration of integrations) {
      expect(
        integration.provider.toLowerCase(),
      ).toBe("toast");

      expect(integration.active).toBe(true);

      expectSafeIntegrationShape(integration);
    }
  });

  test("accepts integration type filter", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/integrations`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          integration_type: "whatsapp",
        },
      },
    );

    expect(response.status()).toBe(200);

    const integrations =
      (await response.json()) as IntegrationResponse[];

    expect(Array.isArray(integrations)).toBe(true);

    for (const integration of integrations) {
      expect(
        integration.integration_type.toLowerCase(),
      ).toBe("whatsapp");

      expectSafeIntegrationShape(integration);
    }
  });

  test("accepts inactive integration filter", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/integrations`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          active: "false",
        },
      },
    );

    expect(response.status()).toBe(200);

    const integrations =
      (await response.json()) as IntegrationResponse[];

    expect(Array.isArray(integrations)).toBe(true);

    for (const integration of integrations) {
      expect(integration.active).toBe(false);
      expectSafeIntegrationShape(integration);
    }
  });

  test("rejects an invalid active filter", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/integrations`,
      {
        headers: getTenantHeaders(accessToken),
        params: {
          active: "invalid",
        },
      },
    );

    expect(response.status()).toBe(422);
  });

  test("returns safe integration detail when records exist", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const headers =
      getTenantHeaders(accessToken);

    const listResponse = await request.get(
      `${API_BASE_URL}/integrations`,
      {
        headers,
      },
    );

    expect(listResponse.status()).toBe(200);

    const integrations =
      (await listResponse.json()) as IntegrationResponse[];

    if (integrations.length === 0) {
      return;
    }

    const integrationId =
      integrations[0].id;

    const detailResponse =
      await request.get(
        `${API_BASE_URL}/integrations/${integrationId}`,
        {
          headers,
        },
      );

    expect(detailResponse.status()).toBe(200);

    const integration =
      (await detailResponse.json()) as IntegrationResponse;

    expect(integration.id).toBe(
      integrationId,
    );

    expectSafeIntegrationShape(integration);

    const serialized =
      JSON.stringify(integration);

    expect(serialized).not.toContain(
      "credentials_env",
    );
  });

  test("returns 404 for an unknown integration", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/integrations/2147483647`,
      {
        headers: getTenantHeaders(accessToken),
      },
    );

    expect(response.status()).toBe(404);
  });

  test("rejects a non-positive integration id", async ({
    request,
  }) => {
    const accessToken =
      await getOwnerAccessToken(request);

    const response = await request.get(
      `${API_BASE_URL}/integrations/0`,
      {
        headers: getTenantHeaders(accessToken),
      },
    );

    expect(response.status()).toBe(422);
  });
});