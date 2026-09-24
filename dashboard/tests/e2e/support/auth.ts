import type {
  APIRequestContext,
  Page,
} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

export const API_BASE_URL = 'http://127.0.0.1:8000';
export const TEST_TENANT = 'lpdb';

const ACCESS_TOKEN_KEY = 'lpdb.dashboard.access_token';
const TENANT_KEY = 'lpdb.dashboard.tenant';

interface OwnerCredentials {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

function parseEnvFile(
  filePath: string,
): Record<string, string> {
  const content = fs.readFileSync(filePath, 'utf8');
  const values: Record<string, string> = {};

  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();

    if (!line || line.startsWith('#')) {
      continue;
    }

    const separatorIndex = line.indexOf('=');

    if (separatorIndex === -1) {
      continue;
    }

    const key = line.slice(0, separatorIndex).trim();
    let value = line.slice(separatorIndex + 1).trim();

    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    values[key] = value;
  }

  return values;
}

function getProjectRoot(): string {
  const cwd = process.cwd();

  if (path.basename(cwd).toLowerCase() === 'dashboard') {
    return path.resolve(cwd, '..');
  }

  return cwd;
}

function getOwnerCredentials(): OwnerCredentials {
  const environmentEmail = process.env.OWNER_EMAIL;
  const environmentPassword = process.env.OWNER_PASSWORD;

  if (environmentEmail && environmentPassword) {
    return {
      email: environmentEmail,
      password: environmentPassword,
    };
  }

  const envPath = path.join(getProjectRoot(), '.env');

  if (!fs.existsSync(envPath)) {
    throw new Error(
      'No se encontro .env y OWNER_EMAIL/OWNER_PASSWORD no estan definidos.',
    );
  }

  const env = parseEnvFile(envPath);

  if (!env.OWNER_EMAIL || !env.OWNER_PASSWORD) {
    throw new Error(
      'OWNER_EMAIL y OWNER_PASSWORD son obligatorios para los E2E.',
    );
  }

  return {
    email: env.OWNER_EMAIL,
    password: env.OWNER_PASSWORD,
  };
}

export async function getOwnerAccessToken(
  request: APIRequestContext,
): Promise<string> {
  const credentials = getOwnerCredentials();

  const response = await request.post(
    `${API_BASE_URL}/auth/login`,
    {
      data: credentials,
    },
  );

  if (!response.ok()) {
    throw new Error(
      `E2E owner login failed: ${response.status()} ${await response.text()}`,
    );
  }

  const login = (await response.json()) as LoginResponse;

  if (!login.access_token) {
    throw new Error(
      'E2E owner login response did not contain access_token.',
    );
  }

  return login.access_token;
}

export function getTenantHeaders(
  accessToken: string,
): Record<string, string> {
  return {
    Authorization: `Bearer ${accessToken}`,
    'X-Tenant': TEST_TENANT,
  };
}

export async function authenticateDashboardPage(
  page: Page,
  request: APIRequestContext,
): Promise<string> {
  const accessToken = await getOwnerAccessToken(request);

  await page.addInitScript(
    ({
      token,
      tenant,
      accessTokenKey,
      tenantKey,
    }) => {
      window.sessionStorage.setItem(
        accessTokenKey,
        token,
      );

      window.sessionStorage.setItem(
        tenantKey,
        tenant,
      );
    },
    {
      token: accessToken,
      tenant: TEST_TENANT,
      accessTokenKey: ACCESS_TOKEN_KEY,
      tenantKey: TENANT_KEY,
    },
  );

  return accessToken;
}