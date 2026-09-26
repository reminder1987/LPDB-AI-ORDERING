"use client";

import { useEffect, useState } from "react";

import { useDashboardRole } from "@/components/auth/session/dashboard-session-context";
import {
  getOrder,
  getOrders,
  updateOrderStatus,
  type Order,
} from "@/lib/api";

import { OrderDetailDrawer } from "./order-detail-drawer";
import { OrderMetrics } from "./order-metrics";
import { OrdersTable } from "./orders-table";

const ORDER_MANAGEMENT_ROLES = new Set([
  "owner",
  "admin",
  "manager",
]);

function getOrderErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (!(error instanceof Error)) {
    return fallback;
  }

  if (error.message === "AUTH_REQUIRED") {
    return "La sesion expiro. Inicia sesion nuevamente.";
  }

  if (
    error.message === "PERMISSION_DENIED" ||
    error.message.includes("API error 403")
  ) {
    return "No tienes permisos para realizar esta accion.";
  }

  return error.message || fallback;
}

export function OrderDashboard() {
  const role = useDashboardRole();
  const canManageOrders = ORDER_MANAGEMENT_ROLES.has(
    role.trim().toLowerCase(),
  );

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
    let active = true;

    getOrders()
      .then((response) => {
        if (!active) {
          return;
        }

        setOrders(response.orders);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!active) {
          return;
        }

        setError(
          getOrderErrorMessage(
            err,
            "No fue posible cargar los pedidos.",
          ),
        );
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
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
        getOrderErrorMessage(
          err,
          "No fue posible cargar el detalle del pedido.",
        ),
      );
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleUpdateOrderStatus(
    orderId: number,
    newStatus: string,
  ) {
    if (!canManageOrders) {
      setStatusError(
        "No tienes permisos para modificar pedidos.",
      );
      return;
    }

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
        getOrderErrorMessage(
          err,
          "No fue posible actualizar el estado del pedido.",
        ),
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
    <div className="min-h-full bg-zinc-100 p-5 text-zinc-950 md:p-8">
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

          {!canManageOrders && (
            <div
              className="mt-4 max-w-2xl rounded-lg border border-zinc-200 bg-white px-4 py-3"
              role="status"
            >
              <p className="text-sm font-medium text-zinc-700">
                Acceso de solo lectura
              </p>

              <p className="mt-1 text-xs leading-5 text-zinc-500">
                Tu rol permite consultar pedidos, pero no modificar
                su estado.
              </p>
            </div>
          )}
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
        canManageOrders={canManageOrders}
        onClose={handleCloseOrder}
        onUpdateStatus={handleUpdateOrderStatus}
      />
    </div>
  );
}
