import type { Order } from "@/lib/api";

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
        <div className="flex min-h-48 items-center justify-center px-5 py-12">
          <div className="text-center">
            <p className="text-sm font-medium text-zinc-600">
              Cargando pedidos
            </p>

            <p className="mt-1 text-xs text-zinc-400">
              Consultando el backend LPDB.
            </p>
          </div>
        </div>
      )}

      {!loading && error && (
        <div className="flex min-h-48 items-center justify-center px-5 py-12">
          <div className="text-center">
            <p className="text-sm font-medium text-red-600">
              No fue posible cargar los pedidos
            </p>

            <p className="mt-2 max-w-xl text-xs text-zinc-400">
              {error}
            </p>
          </div>
        </div>
      )}

      {!loading && !error && orders.length === 0 && (
        <div className="flex min-h-48 items-center justify-center px-5 py-12">
          <div className="text-center">
            <p className="text-sm font-medium text-zinc-600">
              No hay pedidos
            </p>

            <p className="mt-1 text-xs text-zinc-400">
              Los pedidos recibidos apareceran aqui.
            </p>
          </div>
        </div>
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