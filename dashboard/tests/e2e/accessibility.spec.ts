import {
  expect,
  test,
} from "@playwright/test";

import { authenticateDashboardPage } from "./support/auth";


test.describe("accesibilidad basica del dashboard", () => {
  test("el menu movil cierra con Escape y devuelve el foco al disparador", async ({
    page,
    request,
  }) => {
    await page.setViewportSize({
      width: 390,
      height: 844,
    });

    await authenticateDashboardPage(
      page,
      request,
    );

    await page.goto("/pedidos");

    const menuButton = page.getByRole("button", {
      name: /menu|navegacion/i,
    });

    await expect(menuButton).toBeVisible();
    await expect(menuButton).toHaveAttribute(
      "aria-expanded",
      "false",
    );

    await menuButton.focus();
    await menuButton.press("Enter");

    await expect(menuButton).toHaveAttribute(
      "aria-expanded",
      "true",
    );

    await page.keyboard.press("Escape");

    await expect(menuButton).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    await expect(menuButton).toBeFocused();
  });


  test("el detalle de pedido gestiona foco, Escape y restauracion", async ({
    page,
    request,
  }) => {
    await page.setViewportSize({
      width: 1440,
      height: 900,
    });

    await authenticateDashboardPage(
      page,
      request,
    );

    await page.goto("/pedidos");

    await expect(
      page.getByRole("heading", {
        name: "Pedidos",
        exact: true,
      }),
    ).toBeVisible();

    const orderTrigger = page
      .getByRole("button", {
        name: /abrir pedido/i,
      })
      .first();

    await expect(orderTrigger).toBeVisible();

    await orderTrigger.focus();
    await expect(orderTrigger).toBeFocused();

    await orderTrigger.press("Enter");

    const dialog = page.getByRole("dialog");

    await expect(dialog).toBeVisible();

    const closeButton = dialog.getByRole("button", {
      name: "Cerrar",
      exact: true,
    });

    await expect(closeButton).toBeFocused();

    await page.keyboard.press("Escape");

    await expect(dialog).toBeHidden();
    await expect(orderTrigger).toBeFocused();
  });
});
