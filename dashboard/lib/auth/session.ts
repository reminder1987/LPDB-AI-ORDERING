const ACCESS_TOKEN_KEY = "lpdb.dashboard.access_token";
const TENANT_KEY = "lpdb.dashboard.tenant";

export const DEFAULT_TENANT = "lpdb";

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface AuthenticatedUser {
  id: number;
  email: string;
  active: boolean;
}

export interface TenantAccess {
  user_id: number;
  tenant_id: number;
  tenant_slug: string;
  tenant_name: string;
  role: string;
}

function canUseBrowserStorage(): boolean {
  return typeof window !== "undefined";
}

export function getAccessToken(): string | null {
  if (!canUseBrowserStorage()) {
    return null;
  }

  return window.sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(accessToken: string): void {
  if (!canUseBrowserStorage()) {
    return;
  }

  window.sessionStorage.setItem(
    ACCESS_TOKEN_KEY,
    accessToken,
  );
}

export function clearAccessToken(): void {
  if (!canUseBrowserStorage()) {
    return;
  }

  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
}

export function getActiveTenant(): string {
  if (!canUseBrowserStorage()) {
    return DEFAULT_TENANT;
  }

  return (
    window.sessionStorage.getItem(TENANT_KEY) ??
    DEFAULT_TENANT
  );
}

export function setActiveTenant(tenant: string): void {
  if (!canUseBrowserStorage()) {
    return;
  }

  window.sessionStorage.setItem(
    TENANT_KEY,
    tenant,
  );
}

export function clearSession(): void {
  if (!canUseBrowserStorage()) {
    return;
  }

  window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  window.sessionStorage.removeItem(TENANT_KEY);
}
