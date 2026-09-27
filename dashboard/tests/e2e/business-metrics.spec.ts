import { expect, test } from "@playwright/test";

import {
  authenticateDashboardPage,
} from "./support/auth";

test(
  "Dashboard de metricas integra resumen, evolucion, sedes y estados",
  async ({ page, request }) => {
    await authenticateDashboardPage(page, request);

    await page.route(
      "**/business-metrics/summary**",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            order_count: 12,
            total_order_value: 480,
            average_ticket: 40,
            status_counts: {
              created: 1,
              confirmed: 1,
              submitting: 1,
              submitted: 7,
              failed: 1,
              cancelled: 1,
            },
          }),
        });
      },
    );

    await page.route(
      "**/business-metrics/evolution**",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              date: "2026-09-20",
              order_count: 5,
              total_order_value: 200,
              average_ticket: 40,
            },
            {
              date: "2026-09-21",
              order_count: 7,
              total_order_value: 280,
              average_ticket: 40,
            },
          ]),
        });
      },
    );

    await page.route(
      "**/business-metrics/locations**",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              location_id: 1,
              location_name: "Wynwood",
              city: "Miami",
              order_count: 8,
              total_order_value: 320,
              average_ticket: 40,
            },
            {
              location_id: 2,
              location_name: "Sunrise",
              city: "Sunrise",
              order_count: 4,
              total_order_value: 160,
              average_ticket: 40,
            },
          ]),
        });
      },
    );

    await page.route(
      "**/business-metrics/conversions**",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            total_orders: 12,
            created_count: 1,
            confirmed_count: 1,
            submitting_count: 1,
            submitted_count: 7,
            failed_count: 1,
            cancelled_count: 1,
            submitted_rate: 0.5833,
            failed_rate: 0.0833,
            cancelled_rate: 0.0833,
          }),
        });
      },
    );

    await page.goto("/metricas");

    await expect(
      page.getByRole("heading", {
        name: "Metricas",
        exact: true,
      }),
    ).toBeVisible();

    await expect(
      page.getByLabel("Resumen comercial"),
    ).toContainText("12");

    await expect(
      page.getByLabel("Resumen comercial"),
    ).toContainText("480");

    await expect(
      page.getByText("Estado actual de pedidos"),
    ).toBeVisible();

    await expect(
      page.getByText("58,3%"),
    ).toBeVisible();

    await expect(
      page.getByText("Evolucion diaria"),
    ).toBeVisible();

    await expect(
      page.getByRole("row").filter({
        hasText: "200",
      }).first(),
    ).toBeVisible();

    await expect(
      page.getByRole("heading", {
        name: "Rendimiento por sede",
        exact: true,
      }),
    ).toBeVisible();

    await expect(
      page.getByText("Wynwood"),
    ).toBeVisible();

    await expect(
      page.getByText("Sunrise", { exact: true }).first(),
    ).toBeVisible();
  },
);

test(
  "Filtro Hasta incluye el dia seleccionado mediante limite exclusivo",
  async ({ page, request }) => {
    await authenticateDashboardPage(page, request);

    const requestedUrls: string[] = [];

    const emptyResponses: Record<string, unknown> = {
      summary: {
        order_count: 0,
        total_order_value: 0,
        average_ticket: 0,
        status_counts: {},
      },
      evolution: [],
      locations: [],
      conversions: {
        total_orders: 0,
        created_count: 0,
        confirmed_count: 0,
        submitting_count: 0,
        submitted_count: 0,
        failed_count: 0,
        cancelled_count: 0,
        submitted_rate: 0,
        failed_rate: 0,
        cancelled_rate: 0,
      },
    };

    await page.route(
      "**/business-metrics/**",
      async (route) => {
        const url = route.request().url();
        requestedUrls.push(url);

        const endpoint = Object.keys(
          emptyResponses,
        ).find((key) => url.includes(`/${key}`));

        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(
            endpoint
              ? emptyResponses[endpoint]
              : {},
          ),
        });
      },
    );

    await page.goto("/metricas");

    await expect(
      page.getByRole("heading", {
        name: "Metricas",
        exact: true,
      }),
    ).toBeVisible();

    await page.getByLabel("Desde").fill("2026-09-01");
    await page.getByLabel("Hasta").fill("2026-09-30");

    requestedUrls.length = 0;

    await page.getByRole("button", {
      name: "Aplicar",
    }).click();

    await expect
      .poll(() => requestedUrls.length)
      .toBeGreaterThanOrEqual(4);

    expect(
      requestedUrls.every((url) => {
        const parsed = new URL(url);

        return (
          parsed.searchParams.get("start_at") ===
            "2026-09-01T00:00:00" &&
          parsed.searchParams.get("end_at") ===
            "2026-10-01T00:00:00"
        );
      }),
    ).toBe(true);
  },
);