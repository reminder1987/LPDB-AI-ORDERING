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

export function OrdersTable({
  orders,
  loading,
  error,
  onOpenOrder,
}: OrdersTableProps) {
  return (
    <div className="mt-6 overflow-hidden rounded-xl border border-zinc-200 bg-white">
      <div className="border-b border-zinc-200 px-5 py-4">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold">
            Pedidos recientes
          </h4>

          {!loading && !error && (
            <span className="text-xs text-zinc-400">
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
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50">
              <tr>
                <th className="px-5 py-3 font-medium text-zinc-500">
                  Pedido
                </th>

                <th className="px-5 py-3 font-medium text-zinc-500">
                  Cliente
                </th>

                <th className="px-5 py-3 font-medium text-zinc-500">
                  Sede
                </th>

                <th className="px-5 py-3 font-medium text-zinc-500">
                  Estado
                </th>

                <th className="px-5 py-3 text-right font-medium text-zinc-500">
                  Total
                </th>
              </tr>
            </thead>

            <tbody>
              {orders
                .slice()
                .reverse()
                .map((order) => (
                  <tr
                    key={order.id}
                    tabIndex={0}
                    role="button"
                    onClick={() => onOpenOrder(order.id)}
                    onKeyDown={(event) => {
                      if (
                        event.key === "Enter" ||
                        event.key === " "
                      ) {
                        event.preventDefault();
                        onOpenOrder(order.id);
                      }
                    }}
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
      )}
    </div>
  );
}