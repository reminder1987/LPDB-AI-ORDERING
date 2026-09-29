import { expect, test } from '@playwright/test';

import {
  authenticateDashboardPage,
} from './support/auth';

const DASHBOARD_ROUTES = [
  {
    path: '/pedidos',
    heading: 'Pedidos',
  },
  {
    path: '/clientes',
    heading: 'Clientes',
  },
  {
    path: '/pagos',
    heading: 'Pagos',
  },
  {
    path: '/metricas',
    heading: 'Metricas',
  },
  {
    path: '/operaciones',
    heading: 'Operaciones',
  },
  {
    path: '/actividad',
    heading: 'Actividad operativa',
  },
  {
    path: '/integraciones',
    heading: 'Integraciones',
  },
] as const;

async function expectNoPageOverflow(
  page: import('@playwright/test').Page,
) {
  const dimensions = await page.evaluate(() => ({
    documentWidth: document.documentElement.scrollWidth,
    viewportWidth: document.documentElement.clientWidth,
  }));

  expect(
    dimensions.documentWidth,
    `La pagina tiene overflow horizontal: ${dimensions.documentWidth}px > ${dimensions.viewportWidth}px`,
  ).toBeLessThanOrEqual(dimensions.viewportWidth);
}

test.describe('responsive dashboard', () => {
  test('rutas principales funcionan en viewport movil sin overflow', async ({
    page,
    request,
  }) => {
    await page.setViewportSize({
      width: 390,
      height: 844,
    });

    await authenticateDashboardPage(page, request);

    for (const route of DASHBOARD_ROUTES) {
      await page.goto(route.path);

      await expect(
        page.getByRole('heading', {
          name: route.heading,
          exact: true,
        }).first(),
      ).toBeVisible();

      await expectNoPageOverflow(page);
    }
  });

  test('navegacion movil abre, navega y cierra correctamente', async ({
    page,
    request,
  }) => {
    await page.setViewportSize({
      width: 390,
      height: 844,
    });

    await authenticateDashboardPage(page, request);
    await page.goto('/');

    await expect(page).toHaveURL(/\/pedidos$/);

    const menuButton = page.getByRole('button', {
      name: /menu|navegacion/i,
    });

    await expect(menuButton).toBeVisible();
    await expect(menuButton).toHaveAttribute(
      'aria-expanded',
      'false',
    );

    await menuButton.click();

    await expect(menuButton).toHaveAttribute(
      'aria-expanded',
      'true',
    );

    const mobileNavigation = page.getByRole('navigation').last();

    await expect(mobileNavigation).toBeVisible();

    await mobileNavigation
      .getByRole('link', {
        name: 'Operaciones',
        exact: true,
      })
      .click();

    await expect(page).toHaveURL(/\/operaciones$/);

    await expect(
      page.getByRole('heading', {
        name: 'Operaciones',
        exact: true,
      }),
    ).toBeVisible();

    await expect(menuButton).toHaveAttribute(
      'aria-expanded',
      'false',
    );

    await expectNoPageOverflow(page);
  });

  test('layout desktop permanece estable', async ({
    page,
    request,
  }) => {
    await page.setViewportSize({
      width: 1440,
      height: 900,
    });

    await authenticateDashboardPage(page, request);
    await page.goto('/pedidos');

    await expect(
      page.getByRole('heading', {
        name: 'Pedidos',
        exact: true,
      }),
    ).toBeVisible();

    await expectNoPageOverflow(page);

    const desktopNavigation = page.getByRole(
      'complementary',
      {
        name: 'Navegacion principal',
      },
    );

    await expect(desktopNavigation).toBeVisible();

    await expect(
      page.getByRole('button', {
        name: /menu|navegacion/i,
      }),
    ).toBeHidden();
  });
});
