"use client";

import { useEffect, useState } from "react";

import {
  getOrder,
  getOrders,
  updateOrderStatus,
  type Order,
} from "@/lib/api";

const menuItems = [
  { label: "Pedidos", active: true },
  { label: "Productos", active: false },
  { label: "Disponibilidad", active: false },
  { label: "Sedes", active: false },
];

function formatCurrency(value: number | null) {
  if (value === null) {
    return "—";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

function formatStatus(status: string) {
  const labels: Record<string, string> = {
    created: "Nuevo",
    confirmed: "Confirmado",
    submitting: "Enviando",
    submitted: "Enviado",
    failed: "Fallido",
    cancelled: "Cancelado",
  };

  return labels[status] ?? status;
}

export default function Home() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [statusUpdating, setStatusUpdating] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);

  useEffect(() => {
    async function loadOrders() {
      try {
        setLoading(true);
        setError(null);

        const response = await getOrders();

        setOrders(response.orders);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "No fue posible cargar los pedidos.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadOrders();
  }, []);

  useEffect(() => {
    if (!selectedOrder && !detailLoading) {
      return;
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setSelectedOrder(null);
        setDetailError(null);
        setStatusError(null);
      }
    }

    window.addEventListener("keydown", handleEscape);

    return () => {
      window.removeEventListener("keydown", handleEscape);
    };
  }, [selectedOrder, detailLoading]);

  async function handleOpenOrder(orderId: number) {
    try {
      setDetailLoading(true);
      setDetailError(null);
      setStatusError(null);
      setSelectedOrder(null);

      const response = await getOrder(orderId);

      setSelectedOrder(response.order);
    } catch (err) {
      setSelectedOrder(null);
      setDetailError(
        err instanceof Error
          ? err.message
          : "No fue posible cargar el detalle del pedido.",
      );
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleUpdateOrderStatus(
    orderId: number,
    newStatus: string,
  ) {
    try {
      setStatusUpdating(true);
      setStatusError(null);

      const response = await updateOrderStatus(
        orderId,
        newStatus,
      );

      setSelectedOrder(response.order);

      setOrders((currentOrders) =>
        currentOrders.map((order) =>
          order.id === response.order.id
            ? response.order
            : order,
        ),
      );
    } catch (err) {
      setStatusError(
        err instanceof Error
          ? err.message
          : "No fue posible actualizar el estado del pedido.",
      );
    } finally {
      setStatusUpdating(false);
    }
  }

  function handleCloseOrder() {
    setSelectedOrder(null);
    setDetailError(null);
    setStatusError(null);
  }

  const createdOrders = orders.filter(
    (order) => order.status === "created",
  ).length;

  const confirmedOrders = orders.filter(
    (order) => order.status === "confirmed",
  ).length;

  const submittingOrders = orders.filter(
    (order) => order.status === "submitting",
  ).length;

  const submittedOrders = orders.filter(
    (order) => order.status === "submitted",
  ).length;

  return (
    <main className="min-h-screen bg-zinc-100 text-zinc-950">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 border-r border-zinc-200 bg-white md:flex md:flex-col">
          <div className="border-b border-zinc-200 px-6 py-5">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
              LPDB
            </p>

            <h1 className="mt-1 text-lg font-bold tracking-tight">
              AI Order Agent
            </h1>
          </div>

          <nav className="flex-1 px-3 py-5">
            <p className="px-3 pb-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Operación
            </p>

            <div className="space-y-1">
              {menuItems.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  className={`w-full rounded-lg px-3 py-2.5 text-left text-sm font-medium transition ${
                    item.active
                      ? "bg-zinc-950 text-white"
                      : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950"
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </nav>

          <div className="border-t border-zinc-200 px-6 py-4">
            <p className="text-xs text-zinc-400">Tenant</p>
            <p className="mt-1 text-sm font-semibold">LPDB</p>
          </div>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <header className="flex min-h-16 items-center justify-between border-b border-zinc-200 bg-white px-5 md:px-8">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                Restaurante
              </p>

              <h2 className="text-base font-semibold">
                Panel operativo
              </h2>
            </div>

            <div className="flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-xs font-medium text-zinc-600">
                Backend operativo
              </span>
            </div>
          </header>

          <div className="flex-1 p-5 md:p-8">
            <div className="mx-auto max-w-7xl">
              <div className="mb-8">
                <p className="text-sm font-medium text-zinc-500">
                  Operación
                </p>

                <h3 className="mt-1 text-3xl font-bold tracking-tight">
                  Pedidos
                </h3>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
                  Consulta y gestiona los pedidos recibidos por LPDB AI
                  Order Agent.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl border border-zinc-200 bg-white p-5">
                  <p className="text-sm text-zinc-500">Todos</p>
                  <p className="mt-2 text-3xl font-bold">
                    {loading ? "—" : orders.length}
                  </p>
                </div>

                <div className="rounded-xl border border-zinc-200 bg-white p-5">
                  <p className="text-sm text-zinc-500">Nuevos</p>
                  <p className="mt-2 text-3xl font-bold">
                    {loading ? "—" : createdOrders}
                  </p>
                </div>

                <div className="rounded-xl border border-zinc-200 bg-white p-5">
                  <p className="text-sm text-zinc-500">Confirmados</p>
                  <p className="mt-2 text-3xl font-bold">
                    {loading ? "—" : confirmedOrders}
                  </p>
                </div>

                <div className="rounded-xl border border-zinc-200 bg-white p-5">
                  <p className="text-sm text-zinc-500">Enviados</p>
                  <p className="mt-2 text-3xl font-bold">
                    {loading ? "—" : submittedOrders}
                  </p>
                </div>
              </div>

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
                        Los pedidos recibidos aparecerán aquí.
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
                              onClick={() => handleOpenOrder(order.id)}
                              onKeyDown={(event) => {
                                if (
                                  event.key === "Enter" ||
                                  event.key === " "
                                ) {
                                  event.preventDefault();
                                  handleOpenOrder(order.id);
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

              {!loading && !error && submittingOrders > 0 && (
                <div className="mt-4 text-xs text-zinc-400">
                  {submittingOrders} pedido(s) en proceso de envío.
                </div>
              )}
            </div>
          </div>
        </section>
      </div>

      {(selectedOrder || detailLoading || detailError) && (
        <div
          className="fixed inset-0 z-50 flex justify-end bg-black/20"
          onClick={handleCloseOrder}
        >
          <aside
            className="flex h-full w-full max-w-xl flex-col bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                  Detalle
                </p>

                <h4 className="mt-1 text-lg font-semibold">
                  {selectedOrder
                    ? `Pedido #${selectedOrder.id}`
                    : "Pedido"}
                </h4>
              </div>

              <button
                type="button"
                onClick={handleCloseOrder}
                className="rounded-lg border border-zinc-200 px-3 py-2 text-sm font-medium text-zinc-600 transition hover:bg-zinc-100 hover:text-zinc-950"
              >
                Cerrar
              </button>
            </div>

            {detailLoading && (
              <div className="flex flex-1 items-center justify-center p-6">
                <div className="text-center">
                  <p className="text-sm font-medium text-zinc-600">
                    Cargando pedido
                  </p>

                  <p className="mt-1 text-xs text-zinc-400">
                    Consultando el backend LPDB.
                  </p>
                </div>
              </div>
            )}

            {!detailLoading && detailError && (
              <div className="flex flex-1 items-center justify-center p-6">
                <div className="max-w-sm text-center">
                  <p className="text-sm font-medium text-red-600">
                    No fue posible cargar el pedido
                  </p>

                  <p className="mt-2 text-xs leading-5 text-zinc-500">
                    {detailError}
                  </p>

                  <button
                    type="button"
                    onClick={handleCloseOrder}
                    className="mt-5 rounded-lg border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100"
                  >
                    Cerrar
                  </button>
                </div>
              </div>
            )}

            {!detailLoading && !detailError && selectedOrder && (
              <div className="flex-1 overflow-y-auto">
                <div className="grid grid-cols-2 border-b border-zinc-200">
                  <div className="border-r border-zinc-200 p-5">
                    <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                      Cliente
                    </p>

                    <p className="mt-1 text-sm font-semibold">
                      {selectedOrder.customer_name || "Sin cliente"}
                    </p>
                  </div>

                  <div className="p-5">
                    <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                      Estado
                    </p>

                    <span className="mt-1 inline-flex rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
                      {formatStatus(selectedOrder.status)}
                    </span>
                  </div>

                  <div className="border-r border-t border-zinc-200 p-5">
                    <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                      Sede
                    </p>

                    <p className="mt-1 text-sm font-semibold">
                      {selectedOrder.location_id
                        ? `Sede ${selectedOrder.location_id}`
                        : "Sin sede"}
                    </p>
                  </div>

                  <div className="border-t border-zinc-200 p-5">
                    <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                      Total
                    </p>

                    <p className="mt-1 text-lg font-bold">
                      {formatCurrency(selectedOrder.total)}
                    </p>
                  </div>
                </div>

                <div className="border-b border-zinc-200 p-5">
                  <h5 className="text-sm font-semibold">
                    Productos
                  </h5>

                  <div className="mt-4 space-y-4">
                    {selectedOrder.items.map((item, index) => (
                      <div
                        key={`${selectedOrder.id}-${item.product}-${index}`}
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
                                (modification, modificationIndex) => (
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
                                      ? ` → ${modification.new_base}`
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
                              {item.combo.requested ? "Sí" : "No"}
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
                  <div className="flex items-center justify-between">
                    <div>
                      <h5 className="text-sm font-semibold">
                        Acciones
                      </h5>

                      <p className="mt-1 text-xs text-zinc-400">
                        Las transiciones son validadas por el backend.
                      </p>
                    </div>
                  </div>

                  {statusError && (
                    <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3">
                      <p className="text-sm font-medium text-red-700">
                        No fue posible actualizar el pedido
                      </p>

                      <p className="mt-1 text-xs leading-5 text-red-600">
                        {statusError}
                      </p>
                    </div>
                  )}

                  {selectedOrder.status === "created" && (
                    <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                      <button
                        type="button"
                        disabled={statusUpdating}
                        onClick={() =>
                          handleUpdateOrderStatus(
                            selectedOrder.id,
                            "confirmed",
                          )
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
                          handleUpdateOrderStatus(
                            selectedOrder.id,
                            "cancelled",
                          )
                        }
                        className="flex-1 rounded-lg border border-zinc-300 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        Cancelar pedido
                      </button>
                    </div>
                  )}

                  {selectedOrder.status === "confirmed" && (
                    <div className="mt-4">
                      <button
                        type="button"
                        disabled={statusUpdating}
                        onClick={() =>
                          handleUpdateOrderStatus(
                            selectedOrder.id,
                            "cancelled",
                          )
                        }
                        className="w-full rounded-lg border border-zinc-300 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {statusUpdating
                          ? "Actualizando..."
                          : "Cancelar pedido"}
                      </button>
                    </div>
                  )}

                  {(selectedOrder.status === "submitting" ||
                    selectedOrder.status === "submitted" ||
                    selectedOrder.status === "failed" ||
                    selectedOrder.status === "cancelled") && (
                    <div className="mt-4 rounded-lg bg-zinc-50 px-4 py-3">
                      <p className="text-sm font-medium text-zinc-600">
                        No hay acciones manuales disponibles para este
                        estado.
                      </p>
                    </div>
                  )}
                </div>

                <div className="bg-zinc-50 p-5">
                  <div className="ml-auto max-w-xs space-y-2">
                    <div className="flex items-center justify-between text-sm text-zinc-500">
                      <span>Subtotal</span>

                      <span>
                        {formatCurrency(selectedOrder.subtotal)}
                      </span>
                    </div>

                    <div className="flex items-center justify-between border-t border-zinc-200 pt-3 text-base font-bold">
                      <span>Total</span>

                      <span>
                        {formatCurrency(selectedOrder.total)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </aside>
        </div>
      )}
    </main>
  );
}