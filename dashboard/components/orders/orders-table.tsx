import type { Order } from "@/lib/api";

import { DashboardState } from "@/components/ui/dashboard-state";

import {
  formatCurrency,
  formatStatus,
} from "./order-formatters";

type OrdersTableProps = {
  orders: Order[];
  loading: boolean;
  error: string | null;
  onOpenOrder: (orderId: number) => void;
};

function handleOrderKeyDown(
  event: React.KeyboardEvent<HTMLElement>,
  orderId: number,
  onOpenOrder: (orderId: number) => void,
) {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    onOpenOrder(orderId);
  }
}

export function OrdersTable({
  orders,
  loading,
  error,
  onOpenOrder,
}: OrdersTableProps) {
  const recentOrders = orders.slice().reverse();

  return (
    <section
      className="mt-6 overflow-hidden rounded-xl border border-zinc-200 bg-white"
      aria-labelledby="recent-orders-heading"
    >
      <div className="border-b border-zinc-200 px-4 py-4 sm:px-5">
        <div className="flex items-center justify-between gap-4">
          <h4
            id="recent-orders-heading"
            className="text-sm font-semibold"
          >
            Pedidos recientes
          </h4>

          {!loading && !error && (
            <span className="shrink-0 text-xs text-zinc-400">
              {orders.length} pedidos
            </span>
          )}
        </div>
      </div>

      {loading && (
        <DashboardState
          variant="loading"
          title="Cargando pedidos"
          description="Consultando el backend LPDB."
        />
      )}

      {!loading && error && (
        <DashboardState
          variant="error"
          title="No fue posible cargar los pedidos"
          description={error}
        />
      )}

      {!loading && !error && orders.length === 0 && (
        <DashboardState
          variant="empty"
          title="No hay pedidos"
          description="Los pedidos recibidos apareceran aqui."
        />
      )}

      {!loading && !error && orders.length > 0 && (
        <>
          <div className="divide-y divide-zinc-100 md:hidden">
            {recentOrders.map((order) => (
              <article
                key={order.id}
                tabIndex={0}
                role="button"
                aria-label={`Abrir pedido ${order.id}`}
                onClick={() => onOpenOrder(order.id)}
                onKeyDown={(event) =>
                  handleOrderKeyDown(
                    event,
                    order.id,
                    onOpenOrder,
                  )
                }
                className="cursor-pointer px-4 py-4 transition hover:bg-zinc-50 focus:bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-zinc-400"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-zinc-950">
                      Pedido #{order.id}
                    </p>

                    <p className="mt-1 truncate text-sm text-zinc-600">
                      {order.customer_name || "Sin cliente"}
                    </p>
                  </div>

                  <span className="shrink-0 rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
                    {formatStatus(order.status)}
                  </span>
                </div>

                <div className="mt-4 flex items-end justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">
                      Sede
                    </p>

                    <p className="mt-1 truncate text-sm text-zinc-600">
                      {order.location_id
                        ? `Sede ${order.location_id}`
                        : "Sin sede"}
                    </p>
                  </div>

                  <div className="shrink-0 text-right">
                    <p className="text-xs font-medium uppercase tracking-wide text-zinc-400">
                      Total
                    </p>

                    <p className="mt-1 text-base font-semibold text-zinc-950">
                      {formatCurrency(order.total)}
                    </p>
                  </div>
                </div>
              </article>
            ))}
          </div>

          <div className="hidden overflow-x-auto md:block">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50">
                <tr>
                  <th
                    scope="col"
                    className="px-5 py-3 font-medium text-zinc-500"
                  >
                    Pedido
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 font-medium text-zinc-500"
                  >
                    Cliente
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 font-medium text-zinc-500"
                  >
                    Sede
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 font-medium text-zinc-500"
                  >
                    Estado
                  </th>

                  <th
                    scope="col"
                    className="px-5 py-3 text-right font-medium text-zinc-500"
                  >
                    Total
                  </th>
                </tr>
              </thead>

              <tbody>
                {recentOrders.map((order) => (
                  <tr
                    key={order.id}
                    tabIndex={0}
                    role="button"
                    aria-label={`Abrir pedido ${order.id}`}
                    onClick={() => onOpenOrder(order.id)}
                    onKeyDown={(event) =>
                      handleOrderKeyDown(
                        event,
                        order.id,
                        onOpenOrder,
                      )
                    }
                    className="cursor-pointer border-b border-zinc-100 transition last:border-b-0 hover:bg-zinc-50 focus:bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-zinc-300"
                  >
                    <td className="px-5 py-4 font-semibold">
                      #{order.id}
                    </td>

                    <td className="px-5 py-4 text-zinc-700">
                      {order.customer_name || "Sin cliente"}
                    </td>

                    <td className="px-5 py-4 text-zinc-500">
                      {order.location_id
                        ? `Sede ${order.location_id}`
                        : "Sin sede"}
                    </td>

                    <td className="px-5 py-4">
                      <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
                        {formatStatus(order.status)}
                      </span>
                    </td>

                    <td className="px-5 py-4 text-right font-semibold">
                      {formatCurrency(order.total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}