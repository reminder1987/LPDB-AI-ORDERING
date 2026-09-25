import { test, expect } from '@playwright/test';

import {
  authenticateDashboardPage,
} from './support/auth';

test(
  'Dashboard carga el modulo de operaciones',
  async ({ page, request }) => {
    await authenticateDashboardPage(page, request);

    const incidentsResponse = page.waitForResponse(
      (response) =>
        response.url().includes(
          '/operational/incidents',
        ) &&
        response.request().method() === 'GET',
    );

    await page.goto('/operaciones');

    await expect(
      page.getByRole('heading', {
        name: 'Operaciones',
        exact: true,
      }),
    ).toBeVisible();

    const response = await incidentsResponse;

    expect(response.status()).toBe(200);

    await expect(
      page.getByLabel('Filtros de incidentes'),
    ).toBeVisible();

    await expect(
      page.getByLabel('Resumen de incidentes'),
    ).toBeVisible();

    await expect(
      page.getByLabel('Estado'),
    ).toBeVisible();

    await expect(
      page.getByLabel('Severidad'),
    ).toBeVisible();

    await expect(
      page.getByLabel('Categoria'),
    ).toBeVisible();
  },
);

test(
  'Dashboard filtra incidentes operacionales',
  async ({ page, request }) => {
    await authenticateDashboardPage(page, request);

    await page.goto('/operaciones');

    await expect(
      page.getByRole('heading', {
        name: 'Operaciones',
        exact: true,
      }),
    ).toBeVisible();

    const filteredResponse = page.waitForResponse(
      (response) => {
        const url = new URL(response.url());

        return (
          url.pathname === '/operational/incidents' &&
          url.searchParams.get('status') === 'open' &&
          response.request().method() === 'GET'
        );
      },
    );

    await page
      .getByLabel('Estado')
      .selectOption('open');

    const response = await filteredResponse;

    expect(response.status()).toBe(200);

    await expect(
      page.getByLabel('Estado'),
    ).toHaveValue('open');
  },
);

test(
  'Dashboard abre el detalle cuando existen incidentes',
  async ({ page, request }) => {
    await authenticateDashboardPage(page, request);

    await page.goto('/operaciones');

    await expect(
      page.getByRole('heading', {
        name: 'Operaciones',
        exact: true,
      }),
    ).toBeVisible();

    const incidentRows = page.locator(
      'tbody tr[role="button"]',
    );

    const emptyState = page.getByText(
      'No hay incidentes para mostrar.',
      {
        exact: true,
      },
    );

    await expect
      .poll(async () => {
        const rowCount = await incidentRows.count();

        if (rowCount > 0) {
          return 'rows';
        }

        if (await emptyState.isVisible()) {
          return 'empty';
        }

        return 'loading';
      })
      .not.toBe('loading');

    const rowCount = await incidentRows.count();

    if (rowCount === 0) {
      await expect(emptyState).toBeVisible();
      return;
    }

    const firstIncident = incidentRows.first();

    await expect(firstIncident).toBeVisible();

    await firstIncident.click();

    await expect(
      page.getByRole('dialog'),
    ).toBeVisible();

    await expect(
      page.getByRole('button', {
        name: 'Cerrar',
        exact: true,
      }),
    ).toBeVisible();

    await expect(
      page.getByText('Identificacion', {
        exact: true,
      }),
    ).toBeVisible();

    await expect(
      page.getByText('Incident ID', {
        exact: true,
      }),
    ).toBeVisible();
  },
);