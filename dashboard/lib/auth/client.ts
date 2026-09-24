import {
  clearSession,
  getAccessToken,
  getActiveTenant,
  setAccessToken,
  setActiveTenant,
  type AuthenticatedUser,
  type LoginCredentials,
  type LoginResponse,
  type TenantAccess,
} from "./session";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

async function parseApiError(
  response: Response,
): Promise<Error> {
  const body = await response.text();

  return new Error(
    `API error ${response.status}: ${
      body || response.statusText
    }`,
  );
}

export async function login(
  credentials: LoginCredentials,
): Promise<LoginResponse> {
  const response = await fetch(
    `${API_BASE_URL}/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(credentials),
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw await parseApiError(response);
  }

  const result =
    (await response.json()) as LoginResponse;

  if (!result.access_token) {
    throw new Error(
      "La respuesta de autenticación no contiene access_token.",
    );
  }

  setAccessToken(result.access_token);

  return result;
}

export async function getCurrentUser(): Promise<AuthenticatedUser> {
  const accessToken = getAccessToken();

  if (!accessToken) {
    throw new Error("AUTH_REQUIRED");
  }

  const response = await fetch(
    `${API_BASE_URL}/auth/me`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      cache: "no-store",
    },
  );

  if (response.status === 401) {
    clearSession();
    throw new Error("AUTH_REQUIRED");
  }

  if (!response.ok) {
    throw await parseApiError(response);
  }

  return response.json() as Promise<AuthenticatedUser>;
}

export async function getTenantAccess(
  tenant = getActiveTenant(),
): Promise<TenantAccess> {
  const accessToken = getAccessToken();

  if (!accessToken) {
    throw new Error("AUTH_REQUIRED");
  }

  const response = await fetch(
    `${API_BASE_URL}/auth/tenant-access`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "X-Tenant": tenant,
      },
      cache: "no-store",
    },
  );

  if (response.status === 401) {
    clearSession();
    throw new Error("AUTH_REQUIRED");
  }

  if (!response.ok) {
    throw await parseApiError(response);
  }

  const access =
    (await response.json()) as TenantAccess;

  setActiveTenant(access.tenant_slug);

  return access;
}

export async function establishSession(
  credentials: LoginCredentials,
): Promise<{
  user: AuthenticatedUser;
  tenant: TenantAccess;
}> {
  await login(credentials);

  try {
    const [user, tenant] = await Promise.all([
      getCurrentUser(),
      getTenantAccess(),
    ]);

    return {
      user,
      tenant,
    };
  } catch (error) {
    clearSession();
    throw error;
  }
}

export function logout(): void {
  clearSession();
}
