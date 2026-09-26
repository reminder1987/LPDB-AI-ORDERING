import type { Payment } from "@/lib/api";

type PaymentDetailDrawerProps = {
  payment: Payment | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
};

function formatAmount(
  amount: number,
  currency: string,
): string {
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
    }).format(Number(amount));
  } catch {
    return `${currency} ${Number(amount).toFixed(2)}`;
  }
}

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "long",
    timeStyle: "medium",
  }).format(date);
}

function formatStatus(status: string): string {
  const labels: Record<string, string> = {
    pending: "Pendiente",
    processing: "Procesando",
    paid: "Pagado",
    failed: "Fallido",
    cancelled: "Cancelado",
    refunded: "Reembolsado",
  };

  return labels[status] ?? status;
}

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="border-b border-zinc-100 py-4 last:border-b-0">
      <dt className="text-xs font-medium uppercase tracking-wide text-zinc-500">
        {label}
      </dt>

      <dd className="mt-1 break-words text-sm font-medium text-zinc-900">
        {value}
      </dd>
    </div>
  );
}

export function PaymentDetailDrawer({
  payment,
  loading,
  error,
  onClose,
}: PaymentDetailDrawerProps) {
  const open =
    payment !== null ||
    loading ||
    error !== null;

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end"
      role="presentation"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
        aria-label="Cerrar detalle del pago"
      />

      <aside
        className="relative z-10 flex h-full w-full max-w-lg flex-col bg-white shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="payment-detail-title"
      >
        <div className="flex items-start justify-between gap-4 border-b border-zinc-200 px-5 py-5">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Pagos
            </p>

            <h4
              id="payment-detail-title"
              className="mt-1 text-xl font-bold tracking-tight text-zinc-950"
            >
              {payment
                ? `Pago #${payment.id}`
                : "Detalle del pago"}
            </h4>

            <p className="mt-1 text-sm text-zinc-500">
              Informacion operacional de solo lectura.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
          >
            Cerrar
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-5">
          {loading ? (
            <div
              className="space-y-4"
              role="status"
              aria-label="Cargando detalle del pago"
            >
              {Array.from({
                length: 7,
              }).map((_, index) => (
                <div
                  key={index}
                  className="rounded-lg border border-zinc-100 p-4"
                >
                  <div className="h-3 w-24 animate-pulse rounded bg-zinc-200" />
                  <div className="mt-3 h-5 w-40 animate-pulse rounded bg-zinc-200" />
                </div>
              ))}
            </div>
          ) : error ? (
            <div
              className="rounded-lg border border-red-200 bg-red-50 p-4"
              role="alert"
            >
              <p className="text-sm font-semibold text-red-700">
                No fue posible cargar el pago
              </p>

              <p className="mt-2 text-sm leading-6 text-red-600">
                {error}
              </p>
            </div>
          ) : payment ? (
            <>
              <div className="rounded-xl border border-zinc-200 bg-zinc-50 px-4">
                <dl>
                  <DetailRow
                    label="Estado"
                    value={formatStatus(
                      payment.status,
                    )}
                  />

                  <DetailRow
                    label="Monto"
                    value={formatAmount(
                      payment.amount,
                      payment.currency,
                    )}
                  />

                  <DetailRow
                    label="Pedido"
                    value={`#${payment.order_id}`}
                  />

                  <DetailRow
                    label="Proveedor"
                    value={payment.provider}
                  />

                  <DetailRow
                    label="ID externo"
                    value={
                      payment.external_id ??
                      "No asignado"
                    }
                  />

                  <DetailRow
                    label="Creado"
                    value={formatDate(
                      payment.created_at,
                    )}
                  />

                  <DetailRow
                    label="Ultima actualizacion"
                    value={formatDate(
                      payment.updated_at,
                    )}
                  />
                </dl>
              </div>

              <div className="mt-5 rounded-xl border border-zinc-200 p-4">
                <p className="text-sm font-semibold text-zinc-900">
                  Operacion protegida
                </p>

                <p className="mt-2 text-sm leading-6 text-zinc-500">
                  Este panel no permite cobrar,
                  reembolsar ni modificar manualmente
                  el estado del pago. El procesamiento
                  permanece bajo los servicios internos
                  de pagos e integraciones.
                </p>
              </div>
            </>
          ) : null}
        </div>
      </aside>
    </div>
  );
}