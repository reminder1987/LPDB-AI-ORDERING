const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const TENANT = "lpdb";

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

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Tenant": TENANT,
      ...options.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const errorText = await response.text();

    throw new Error(
      `API error ${response.status}: ${errorText || response.statusText}`,
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
  return apiFetch<OrderResponseWrapper>(`/orders/${orderId}`);
}