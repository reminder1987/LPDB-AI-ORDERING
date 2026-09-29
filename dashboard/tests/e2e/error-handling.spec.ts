import { expect, test } from "@playwright/test";

import { authenticateDashboardPage } from "./support/auth";

test.describe("manejo de errores del dashboard", () => {
  test("muestra un estado controlado cuando pedidos responde 500", async ({
    page,
    request,
  }) => {
    await authenticateDashboardPage(page, request);

    await page.route("**/orders/**", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Internal Server Error",
        }),
      });
    });

    await page.goto("/pedidos");

    await expect(
      page.getByRole("heading", {
        name: "Pedidos",
        exact: true,
      }),
    ).toBeVisible();

    const ordersRegion = page.getByRole("region", {
      name: "Pedidos recientes",
    });

    await expect(
      ordersRegion.getByRole("alert"),
    ).toContainText(
      "No fue posible cargar los pedidos",
    );

    await expect(
      page.getByText("Error inesperado", {
        exact: true,
      }),
    ).toHaveCount(0);
  });

  test("maneja de forma controlada una sesion expirada", async ({
    page,
    request,
  }) => {
    await authenticateDashboardPage(page, request);

    await page.route("**/orders/**", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Unauthorized",
        }),
      });
    });

    await page.goto("/pedidos");

    await expect(
      page.getByRole("heading", {
        name: "Pedidos",
        exact: true,
      }),
    ).toBeVisible();

    const ordersRegion = page.getByRole("region", {
      name: "Pedidos recientes",
    });

    await expect(
      ordersRegion.getByRole("alert"),
    ).toContainText(
      "La sesion expiro. Inicia sesion nuevamente.",
    );
  });

  test("muestra un estado controlado cuando el usuario no tiene permiso", async ({
    page,
    request,
  }) => {
    await authenticateDashboardPage(page, request);

    await page.route("**/orders/**", async (route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Forbidden",
        }),
      });
    });

    await page.goto("/pedidos");

    await expect(
      page.getByRole("heading", {
        name: "Pedidos",
        exact: true,
      }),
    ).toBeVisible();

    const ordersRegion = page.getByRole("region", {
      name: "Pedidos recientes",
    });

    await expect(
      ordersRegion.getByRole("alert"),
    ).toContainText(
      "No tienes permisos para realizar esta accion.",
    );
  });
});