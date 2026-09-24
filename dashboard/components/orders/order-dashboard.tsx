"use client";

import { useEffect, useState } from "react";

import {
  getOrder,
  getOrders,
  updateOrderStatus,
  type Order,
} from "@/lib/api";

import { OrderDetailDrawer } from "./order-detail-drawer";
import { OrderMetrics } from "./order-metrics";
import { OrdersTable } from "./orders-table";

export function OrderDashboard() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedOrder, setSelectedOrder] =
    useState<Order | null>(null);
  const [detailLoading, setDetailLoading] =
    useState(false);
  const [detailError, setDetailError] =
    useState<string | null>(null);

  const [statusUpdating, setStatusUpdating] =
    useState(false);
  const [statusError, setStatusError] =
    useState<string | null>(null);

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
    <main className="min-h-full bg-zinc-100 p-5 text-zinc-950 md:p-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium text-zinc-500">
            Operacion
          </p>

          <h3 className="mt-1 text-3xl font-bold tracking-tight">
            Pedidos
          </h3>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
            Consulta y gestiona los pedidos recibidos por LPDB AI
            Order Agent.
          </p>
        </div>

        <OrderMetrics
          total={orders.length}
          created={createdOrders}
          confirmed={confirmedOrders}
          submitted={submittedOrders}
          loading={loading}
        />

        <OrdersTable
          orders={orders}
          loading={loading}
          error={error}
          onOpenOrder={handleOpenOrder}
        />

        {!loading && !error && submittingOrders > 0 && (
          <div className="mt-4 text-xs text-zinc-400">
            {submittingOrders} pedido(s) en proceso de envio.
          </div>
        )}
      </div>

      <OrderDetailDrawer
        order={selectedOrder}
        loading={detailLoading}
        error={detailError}
        statusUpdating={statusUpdating}
        statusError={statusError}
        onClose={handleCloseOrder}
        onUpdateStatus={handleUpdateOrderStatus}
      />
    </main>
  );
}