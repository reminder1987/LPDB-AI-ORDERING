import type { Order } from "@/lib/api";

import { DashboardState } from "@/components/ui/dashboard-state";

import {
  formatCurrency,
  formatStatus,
} from "./order-formatters";

type OrderDetailDrawerProps = {
  order: Order | null;
  loading: boolean;
  error: string | null;
  statusUpdating: boolean;
  statusError: string | null;
  onClose: () => void;
  onUpdateStatus: (
    orderId: number,
    newStatus: string,
  ) => void;
};

export function OrderDetailDrawer({
  order,
  loading,
  error,
  statusUpdating,
  statusError,
  onClose,
  onUpdateStatus,
}: OrderDetailDrawerProps) {
  if (!order && !loading && !error) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/20"
      onClick={onClose}
    >
      <aside
        className="flex h-full w-full max-w-xl flex-col bg-white shadow-2xl"
        onClick={(event) => event.stopPropagation()}
        aria-label={
          order
            ? `Detalle del pedido ${order.id}`
            : "Detalle del pedido"
        }
      >
        <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
              Detalle
            </p>

            <h4 className="mt-1 text-lg font-semibold">
              {order ? `Pedido #${order.id}` : "Pedido"}
            </h4>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-zinc-200 px-3 py-2 text-sm font-medium text-zinc-600 transition hover:bg-zinc-100 hover:text-zinc-950"
          >
            Cerrar
          </button>
        </div>

        {loading && (
          <div className="flex flex-1 flex-col">
            <DashboardState
              variant="loading"
              title="Cargando pedido"
              description="Consultando el backend LPDB."
            />
          </div>
        )}

        {!loading && error && (
          <div className="flex flex-1 flex-col">
            <DashboardState
              variant="error"
              title="No fue posible cargar el pedido"
              description={error}
            />

            <div className="px-6 pb-6 text-center">
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100"
              >
                Cerrar
              </button>
            </div>
          </div>
        )}

        {!loading && !error && order && (
          <div className="flex-1 overflow-y-auto">
            <div className="grid grid-cols-2 border-b border-zinc-200">
              <div className="border-r border-zinc-200 p-5">
                <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                  Cliente
                </p>

                <p className="mt-1 text-sm font-semibold">
                  {order.customer_name || "Sin cliente"}
                </p>
              </div>

              <div className="p-5">
                <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                  Estado
                </p>

                <span className="mt-1 inline-flex rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
                  {formatStatus(order.status)}
                </span>
              </div>

              <div className="border-r border-t border-zinc-200 p-5">
                <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                  Sede
                </p>

                <p className="mt-1 text-sm font-semibold">
                  {order.location_id
                    ? `Sede ${order.location_id}`
                    : "Sin sede"}
                </p>
              </div>

              <div className="border-t border-zinc-200 p-5">
                <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                  Total
                </p>

                <p className="mt-1 text-lg font-bold">
                  {formatCurrency(order.total)}
                </p>
              </div>
            </div>

            <div className="border-b border-zinc-200 p-5">
              <h5 className="text-sm font-semibold">
                Productos
              </h5>

              <div className="mt-4 space-y-4">
                {order.items.map((item, index) => (
                  <div
                    key={`${order.id}-${item.product}-${index}`}
                    className="rounded-xl border border-zinc-200 p-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold">
                          {item.product}
                        </p>

                        <p className="mt-1 text-xs text-zinc-500">
                          Cantidad: {item.quantity}
                        </p>
                      </div>

                      <p className="shrink-0 text-sm font-semibold">
                        {formatCurrency(item.subtotal)}
                      </p>
                    </div>

                    {item.modifications.length > 0 && (
                      <div className="mt-4 border-t border-zinc-200 pt-4">
                        <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                          Modificaciones
                        </p>

                        <div className="mt-2 space-y-1.5">
                          {item.modifications.map(
                            (
                              modification,
                              modificationIndex,
                            ) => (
                              <p
                                key={`${modification.type}-${modification.ingredient}-${modificationIndex}`}
                                className="text-sm text-zinc-600"
                              >
                                {modification.type === "REMOVE"
                                  ? "Sin"
                                  : modification.type}
                                {modification.ingredient
                                  ? ` ${modification.ingredient}`
                                  : ""}
                                {modification.new_base
                                  ? ` -> ${modification.new_base}`
                                  : ""}
                              </p>
                            ),
                          )}
                        </div>
                      </div>
                    )}

                    {item.combo && (
                      <div className="mt-4 border-t border-zinc-200 pt-4">
                        <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                          Combo
                        </p>

                        <p className="mt-2 text-sm text-zinc-600">
                          Solicitado:{" "}
                          {item.combo.requested ? "Si" : "No"}
                        </p>

                        {item.combo.fries && (
                          <p className="mt-1 text-sm text-zinc-600">
                            Papas: {item.combo.fries}
                          </p>
                        )}

                        {item.combo.beverage && (
                          <p className="mt-1 text-sm text-zinc-600">
                            Bebida: {item.combo.beverage.product}
                          </p>
                        )}

                        {item.combo.price !== null && (
                          <p className="mt-1 text-sm text-zinc-600">
                            Precio combo:{" "}
                            {formatCurrency(item.combo.price)}
                          </p>
                        )}
                      </div>
                    )}

                    <div className="mt-4 flex items-center justify-between border-t border-zinc-200 pt-3 text-xs text-zinc-500">
                      <span>Precio unitario</span>

                      <span className="font-medium text-zinc-700">
                        {formatCurrency(item.unit_price)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-b border-zinc-200 p-5">
              <div>
                <h5 className="text-sm font-semibold">
                  Acciones
                </h5>

                <p className="mt-1 text-xs text-zinc-400">
                  Las transiciones son validadas por el backend.
                </p>
              </div>

              {statusError && (
                <div
                  className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3"
                  role="alert"
                  aria-live="assertive"
                >
                  <p className="text-sm font-medium text-red-700">
                    No fue posible actualizar el pedido
                  </p>

                  <p className="mt-1 text-xs leading-5 text-red-600">
                    {statusError}
                  </p>
                </div>
              )}

              {order.status === "created" && (
                <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                  <button
                    type="button"
                    disabled={statusUpdating}
                    aria-busy={statusUpdating}
                    onClick={() =>
                      onUpdateStatus(order.id, "confirmed")
                    }
                    className="flex-1 rounded-lg bg-zinc-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {statusUpdating
                      ? "Actualizando..."
                      : "Confirmar pedido"}
                  </button>

                  <button
                    type="button"
                    disabled={statusUpdating}
                    onClick={() =>
                      onUpdateStatus(order.id, "cancelled")
                    }
                    className="flex-1 rounded-lg border border-zinc-300 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Cancelar pedido
                  </button>
                </div>
              )}

              {order.status === "confirmed" && (
                <div className="mt-4">
                  <button
                    type="button"
                    disabled={statusUpdating}
                    aria-busy={statusUpdating}
                    onClick={() =>
                      onUpdateStatus(order.id, "cancelled")
                    }
                    className="w-full rounded-lg border border-zinc-300 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {statusUpdating
                      ? "Actualizando..."
                      : "Cancelar pedido"}
                  </button>
                </div>
              )}

              {(order.status === "submitting" ||
                order.status === "submitted" ||
                order.status === "failed" ||
                order.status === "cancelled") && (
                <div className="mt-4 rounded-lg bg-zinc-50 px-4 py-3">
                  <p className="text-sm font-medium text-zinc-600">
                    No hay acciones manuales disponibles para este estado.
                  </p>
                </div>
              )}
            </div>

            <div className="bg-zinc-50 p-5">
              <div className="ml-auto max-w-xs space-y-2">
                <div className="flex items-center justify-between text-sm text-zinc-500">
                  <span>Subtotal</span>

                  <span>
                    {formatCurrency(order.subtotal)}
                  </span>
                </div>

                <div className="flex items-center justify-between border-t border-zinc-200 pt-3 text-base font-bold">
                  <span>Total</span>

                  <span>
                    {formatCurrency(order.total)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}