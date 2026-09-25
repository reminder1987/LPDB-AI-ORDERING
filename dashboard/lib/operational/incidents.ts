import {
  clearSession,
  getAccessToken,
  getActiveTenant,
} from "@/lib/auth/session";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export type IncidentSeverity =
  | "info"
  | "warning"
  | "critical";

export type IncidentStatus =
  | "open"
  | "resolved";

export type IncidentCategory =
  | "provider"
  | "payment"
  | "order"
  | "webhook"
  | "reconciliation"
  | "system";

export interface OperationalIncident {
  id: string;
  fingerprint: string;
  category: IncidentCategory;
  severity: IncidentSeverity;
  status: IncidentStatus;
  title: string;
  description: string;
  provider: string | null;
  operation: string | null;
  tenant_id: number | null;
  context: Record<string, string>;
  occurrence_count: number;
  first_seen_at: string;
  last_seen_at: string;
  resolved_at: string | null;
}

export interface OperationalIncidentFilters {
  status?: IncidentStatus;
  severity?: IncidentSeverity;
  category?: IncidentCategory;
}

async function operationalFetch<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const accessToken = getAccessToken();

  if (!accessToken) {
    throw new Error("AUTH_REQUIRED");
  }

  const headers = new Headers(options.headers);

  headers.set("Content-Type", "application/json");
  headers.set("X-Tenant", getActiveTenant());
  headers.set(
    "Authorization",
    `Bearer ${accessToken}`,
  );

  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      headers,
      cache: "no-store",
    },
  );

  if (response.status === 401) {
    clearSession();
    throw new Error("AUTH_REQUIRED");
  }

  if (response.status === 403) {
    throw new Error("PERMISSION_DENIED");
  }

  if (!response.ok) {
    const errorText = await response.text();

    throw new Error(
      `API error ${response.status}: ${
        errorText || response.statusText
      }`,
    );
  }

  return response.json() as Promise<T>;
}

function buildIncidentQuery(
  filters: OperationalIncidentFilters,
): string {
  const params = new URLSearchParams();

  if (filters.status) {
    params.set("status", filters.status);
  }

  if (filters.severity) {
    params.set("severity", filters.severity);
  }

  if (filters.category) {
    params.set("category", filters.category);
  }

  const query = params.toString();

  return query ? `?${query}` : "";
}

export async function getOperationalIncidents(
  filters: OperationalIncidentFilters = {},
): Promise<OperationalIncident[]> {
  return operationalFetch<OperationalIncident[]>(
    `/operational/incidents${buildIncidentQuery(filters)}`,
  );
}

export async function getOperationalIncident(
  incidentId: string,
): Promise<OperationalIncident> {
  const normalizedIncidentId = incidentId.trim();

  if (!normalizedIncidentId) {
    throw new Error("INCIDENT_ID_REQUIRED");
  }

  return operationalFetch<OperationalIncident>(
    `/operational/incidents/${encodeURIComponent(
      normalizedIncidentId,
    )}`,
  );
}