"use client";

import { useEffect, useMemo, useState } from "react";

import {
  getPayment,
  getPayments,
  type Payment,
  type PaymentStatus,
} from "@/lib/api";

import { PaymentDetailDrawer } from "./payment-detail-drawer";
import { PaymentMetrics } from "./payment-metrics";
import { PaymentsTable } from "./payments-table";

const PAYMENT_STATUSES: Array<{
  value: PaymentStatus;
  label: string;
}> = [
  {
    value: "pending",
    label: "Pendiente",
  },
  {
    value: "processing",
    label: "Procesando",
  },
  {
    value: "paid",
    label: "Pagado",
  },
  {
    value: "failed",
    label: "Fallido",
  },
  {
    value: "cancelled",
    label: "Cancelado",
  },
  {
    value: "refunded",
    label: "Reembolsado",
  },
];

function getPaymentErrorMessage(
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
    return "No tienes permisos para consultar los pagos.";
  }

  return error.message || fallback;
}

export function PaymentDashboard() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] =
    useState<PaymentStatus | "">("");
  const [providerFilter, setProviderFilter] =
    useState("");

  const [selectedPayment, setSelectedPayment] =
    useState<Payment | null>(null);
  const [detailLoading, setDetailLoading] =
    useState(false);
  const [detailError, setDetailError] =
    useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadPayments() {
      try {
        setLoading(true);
        setError(null);

        const response = await getPayments({
          status: statusFilter || undefined,
          provider: providerFilter || undefined,
        });

        if (!active) {
          return;
        }

        setPayments(response);
      } catch (err) {
        if (!active) {
          return;
        }

        setError(
          getPaymentErrorMessage(
            err,
            "No fue posible cargar los pagos.",
          ),
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadPayments();

    return () => {
      active = false;
    };
  }, [statusFilter, providerFilter]);

  useEffect(() => {
    if (!selectedPayment && !detailLoading) {
      return;
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setSelectedPayment(null);
        setDetailError(null);
      }
    }

    window.addEventListener(
      "keydown",
      handleEscape,
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleEscape,
      );
    };
  }, [selectedPayment, detailLoading]);

  async function handleOpenPayment(
    paymentId: number,
  ) {
    try {
      setDetailLoading(true);
      setDetailError(null);
      setSelectedPayment(null);

      const payment = await getPayment(paymentId);

      setSelectedPayment(payment);
    } catch (err) {
      setSelectedPayment(null);
      setDetailError(
        getPaymentErrorMessage(
          err,
          "No fue posible cargar el detalle del pago.",
        ),
      );
    } finally {
      setDetailLoading(false);
    }
  }

  function handleClosePayment() {
    setSelectedPayment(null);
    setDetailError(null);
  }

  function handleClearFilters() {
    setStatusFilter("");
    setProviderFilter("");
  }

  const metrics = useMemo(() => {
    const paidPayments = payments.filter(
      (payment) => payment.status === "paid",
    );

    const pendingPayments = payments.filter(
      (payment) =>
        payment.status === "pending" ||
        payment.status === "processing",
    );

    const failedPayments = payments.filter(
      (payment) => payment.status === "failed",
    );

    const paidAmount = paidPayments.reduce(
      (total, payment) =>
        total + Number(payment.amount),
      0,
    );

    return {
      total: payments.length,
      paid: paidPayments.length,
      pending: pendingPayments.length,
      failed: failedPayments.length,
      paidAmount,
    };
  }, [payments]);

  return (
    <div className="min-h-full bg-zinc-100 p-5 text-zinc-950 md:p-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <p className="text-sm font-medium text-zinc-500">
            Operacion
          </p>

          <h3 className="mt-1 text-3xl font-bold tracking-tight">
            Pagos
          </h3>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
            Consulta el estado operativo de los pagos asociados
            a los pedidos del restaurante.
          </p>

          <div
            className="mt-4 max-w-2xl rounded-lg border border-zinc-200 bg-white px-4 py-3"
            role="status"
          >
            <p className="text-sm font-medium text-zinc-700">
              Vista operacional de solo lectura
            </p>

            <p className="mt-1 text-xs leading-5 text-zinc-500">
              Los cobros, reembolsos y transiciones internas de
              pagos no se ejecutan manualmente desde este modulo.
            </p>
          </div>
        </div>

        <PaymentMetrics
          total={metrics.total}
          paid={metrics.paid}
          pending={metrics.pending}
          failed={metrics.failed}
          paidAmount={metrics.paidAmount}
          loading={loading}
        />

        <section
          className="mt-6 rounded-xl border border-zinc-200 bg-white p-4 md:p-5"
          aria-labelledby="payment-filters-title"
        >
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end">
            <div className="flex-1">
              <h4
                id="payment-filters-title"
                className="text-sm font-semibold text-zinc-950"
              >
                Filtros
              </h4>

              <p className="mt-1 text-xs text-zinc-500">
                Filtra la operacion por estado o proveedor.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:w-[34rem]">
              <label className="block">
                <span className="text-xs font-medium text-zinc-600">
                  Estado
                </span>

                <select
                  value={statusFilter}
                  onChange={(event) =>
                    setStatusFilter(
                      event.target.value as
                        | PaymentStatus
                        | "",
                    )
                  }
                  className="mt-1 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
                >
                  <option value="">
                    Todos los estados
                  </option>

                  {PAYMENT_STATUSES.map((status) => (
                    <option
                      key={status.value}
                      value={status.value}
                    >
                      {status.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="text-xs font-medium text-zinc-600">
                  Proveedor
                </span>

                <input
                  type="text"
                  value={providerFilter}
                  onChange={(event) =>
                    setProviderFilter(
                      event.target.value,
                    )
                  }
                  placeholder="Ej. toast"
                  className="mt-1 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm outline-none transition placeholder:text-zinc-400 focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200"
                />
              </label>
            </div>

            {(statusFilter || providerFilter) && (
              <button
                type="button"
                onClick={handleClearFilters}
                className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
              >
                Limpiar filtros
              </button>
            )}
          </div>
        </section>

        <PaymentsTable
          payments={payments}
          loading={loading}
          error={error}
          onOpenPayment={handleOpenPayment}
        />
      </div>

      <PaymentDetailDrawer
        payment={selectedPayment}
        loading={detailLoading}
        error={detailError}
        onClose={handleClosePayment}
      />
    </div>
  );
}