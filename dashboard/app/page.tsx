"use client";

import { useEffect, useState } from "react";

import { getOrders, type Order } from "@/lib/api";

const menuItems = [
  { label: "Pedidos", active: true },
  { label: "Productos", active: false },
  { label: "Disponibilidad", active: false },
  { label: "Sedes", active: false },
];

function formatCurrency(value: number) {
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
                              className="border-b border-zinc-100 last:border-b-0"
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
    </main>
  );
}