const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const TENANT = "lpdb";

export interface OrderItemModification {
  modification_type: string;
  ingredient_name: string | null;
  new_base: string | null;
  price: number | null;
}

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
  combo_requested: boolean;
  beverage_product_id: number | null;
  beverage_product_name: string | null;
  modifications: OrderItemModification[];
}

export interface Order {
  id: number;
  status: string;
  tenant_id: number | null;
  customer_id: number | null;
  customer_name: string | null;
  location_id: number | null;
  items: OrderItem[];
  subtotal: number;
  total: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface OrderListResponse {
  orders: Order[];
  total: number;
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