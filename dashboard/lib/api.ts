import {
  clearSession,
  getAccessToken,
  getActiveTenant,
} from "@/lib/auth/session";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export interface OrderModification {
  type: string;
  ingredient: string | null;
  new_base: string | null;
  price: number | null;
}

export interface OrderBeverage {
  product_id: number;
  product: string;
}

export interface OrderCombo {
  requested: boolean;
  fries: string;
  beverage: OrderBeverage | null;
  price: number | null;
}

export interface OrderItem {
  product: string;
  quantity: number;
  modifications: OrderModification[];
  combo: OrderCombo | null;
  unit_price: number | null;
  subtotal: number | null;
}

export interface Order {
  id: number;
  status: string;
  customer_name: string;
  location_id: number | null;

  product: string;
  quantity: number;
  modifications: OrderModification[];
  combo: OrderCombo | null;

  items: OrderItem[];

  subtotal: number | null;
  total: number | null;
}

export interface OrderResponseWrapper {
  status: string;
  order: Order;
}

export interface OrderListResponse {
  status: string;
  orders: Order[];
}

export type PaymentStatus =
  | "pending"
  | "processing"
  | "paid"
  | "failed"
  | "cancelled"
  | "refunded";

export interface Payment {
  id: number;
  order_id: number;
  provider: string;
  external_id: string | null;
  amount: number;
  currency: string;
  status: PaymentStatus;
  created_at: string;
  updated_at: string;
}

export interface PaymentFilters {
  status?: PaymentStatus;
  provider?: string;
}

export interface CustomerIdentity {
  id: number;
  channel: string;
  external_id: string;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: number;
  name: string;
  phone: string | null;
  email: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
  order_count: number;
  order_total: number;
}

export interface CustomerDetail extends Customer {
  identities: CustomerIdentity[];
}

export interface CustomerFilters {
  search?: string;
  active?: boolean;
}

async function apiFetch<T>(
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

export async function getOrders(): Promise<OrderListResponse> {
  return apiFetch<OrderListResponse>("/orders/");
}

export async function getOrder(
  orderId: number,
): Promise<OrderResponseWrapper> {
  return apiFetch<OrderResponseWrapper>(
    `/orders/${orderId}`,
  );
}

export async function updateOrderStatus(
  orderId: number,
  status: string,
): Promise<OrderResponseWrapper> {
  return apiFetch<OrderResponseWrapper>(
    `/orders/${orderId}/status`,
    {
      method: "PATCH",
      body: JSON.stringify({
        status,
      }),
    },
  );
}

export async function getPayments(
  filters: PaymentFilters = {},
): Promise<Payment[]> {
  const searchParams = new URLSearchParams();

  if (filters.status) {
    searchParams.set("status", filters.status);
  }

  if (filters.provider?.trim()) {
    searchParams.set(
      "provider",
      filters.provider.trim(),
    );
  }

  const query = searchParams.toString();

  return apiFetch<Payment[]>(
    query
      ? `/payments?${query}`
      : "/payments",
  );
}

export async function getPayment(
  paymentId: number,
): Promise<Payment> {
  return apiFetch<Payment>(
    `/payments/${paymentId}`,
  );
}

export async function getCustomers(
  filters: CustomerFilters = {},
): Promise<Customer[]> {
  const searchParams = new URLSearchParams();

  if (filters.search?.trim()) {
    searchParams.set(
      "search",
      filters.search.trim(),
    );
  }

  if (filters.active !== undefined) {
    searchParams.set(
      "active",
      String(filters.active),
    );
  }

  const query = searchParams.toString();

  return apiFetch<Customer[]>(
    query
      ? `/customers?${query}`
      : "/customers",
  );
}

export async function getCustomer(
  customerId: number,
): Promise<CustomerDetail> {
  return apiFetch<CustomerDetail>(
    `/customers/${customerId}`,
  );
}