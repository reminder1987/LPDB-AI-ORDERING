import type {
  Payment,
  PaymentStatus,
} from "@/lib/api";

type PaymentsTableProps = {
  payments: Payment[];
  loading: boolean;
  error: string | null;
  onOpenPayment: (paymentId: number) => void;
};

const PAYMENT_STATUS_LABELS: Record<
  PaymentStatus,
  string
> = {
  pending: "Pendiente",
  processing: "Procesando",
  paid: "Pagado",
  failed: "Fallido",
  cancelled: "Cancelado",
  refunded: "Reembolsado",
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

function formatDate(
  value: string,
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function PaymentStatusBadge({
  status,
}: {
  status: PaymentStatus;
}) {
  const styles: Record<
    PaymentStatus,
    string
  > = {
    pending:
      "border-amber-200 bg-amber-50 text-amber-700",
    processing:
      "border-blue-200 bg-blue-50 text-blue-700",
    paid:
      "border-emerald-200 bg-emerald-50 text-emerald-700",
    failed:
      "border-red-200 bg-red-50 text-red-700",
    cancelled:
      "border-zinc-300 bg-zinc-100 text-zinc-600",
    refunded:
      "border-violet-200 bg-violet-50 text-violet-700",
  };

  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${styles[status]}`}
    >
      {PAYMENT_STATUS_LABELS[status]}
    </span>
  );
}

function LoadingRows() {
  return (
    <>
      {Array.from({
        length: 5,
      }).map((_, index) => (
        <tr
          key={index}
          className="border-t border-zinc-100"
        >
          {Array.from({
            length: 7,
          }).map((__, cellIndex) => (
            <td
              key={cellIndex}
              className="px-4 py-4"
            >
              <div
                className="h-4 animate-pulse rounded bg-zinc-200"
                aria-hidden="true"
              />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

export function PaymentsTable({
  payments,
  loading,
  error,
  onOpenPayment,
}: PaymentsTableProps) {
  return (
    <section
      className="mt-6 overflow-hidden rounded-xl border border-zinc-200 bg-white"
      aria-labelledby="payments-table-title"
    >
      <div className="border-b border-zinc-200 px-5 py-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h4
              id="payments-table-title"
              className="text-sm font-semibold text-zinc-950"
            >
              Registro de pagos
            </h4>

            <p className="mt-1 text-xs text-zinc-500">
              Pagos asociados a los pedidos del tenant activo.
            </p>
          </div>

          {!loading && !error && (
            <span className="text-xs font-medium text-zinc-400">
              {payments.length} registro(s)
            </span>
          )}
        </div>
      </div>

      {error ? (
        <div
          className="px-5 py-10 text-center"
          role="alert"
        >
          <p className="text-sm font-medium text-red-700">
            No fue posible cargar los pagos
          </p>

          <p className="mt-2 text-sm text-zinc-500">
            {error}
          </p>
        </div>
      ) : !loading && payments.length === 0 ? (
        <div
          className="px-5 py-12 text-center"
          role="status"
        >
          <p className="text-sm font-medium text-zinc-700">
            No hay pagos para mostrar
          </p>

          <p className="mt-2 text-sm text-zinc-500">
            No encontramos registros con los filtros actuales.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left">
            <thead className="bg-zinc-50">
              <tr className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                <th
                  scope="col"
                  className="whitespace-nowrap px-4 py-3"
                >
                  Pago
                </th>

                <th
                  scope="col"
                  className="whitespace-nowrap px-4 py-3"
                >
                  Pedido
                </th>

                <th
                  scope="col"
                  className="whitespace-nowrap px-4 py-3"
                >
                  Proveedor
                </th>

                <th
                  scope="col"
                  className="whitespace-nowrap px-4 py-3"
                >
                  Estado
                </th>

                <th
                  scope="col"
                  className="whitespace-nowrap px-4 py-3"
                >
                  Monto
                </th>

                <th
                  scope="col"
                  className="whitespace-nowrap px-4 py-3"
                >
                  Actualizado
                </th>

                <th
                  scope="col"
                  className="whitespace-nowrap px-4 py-3 text-right"
                >
                  Accion
                </th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <LoadingRows />
              ) : (
                payments.map((payment) => (
                  <tr
                    key={payment.id}
                    className="border-t border-zinc-100 text-sm text-zinc-700 transition hover:bg-zinc-50"
                  >
                    <td className="whitespace-nowrap px-4 py-4 font-medium text-zinc-950">
                      #{payment.id}
                    </td>

                    <td className="whitespace-nowrap px-4 py-4">
                      #{payment.order_id}
                    </td>

                    <td className="whitespace-nowrap px-4 py-4">
                      {payment.provider}
                    </td>

                    <td className="whitespace-nowrap px-4 py-4">
                      <PaymentStatusBadge
                        status={payment.status}
                      />
                    </td>

                    <td className="whitespace-nowrap px-4 py-4 font-medium text-zinc-950">
                      {formatAmount(
                        payment.amount,
                        payment.currency,
                      )}
                    </td>

                    <td className="whitespace-nowrap px-4 py-4 text-zinc-500">
                      {formatDate(
                        payment.updated_at,
                      )}
                    </td>

                    <td className="whitespace-nowrap px-4 py-4 text-right">
                      <button
                        type="button"
                        onClick={() =>
                          onOpenPayment(
                            payment.id,
                          )
                        }
                        className="rounded-lg border border-zinc-300 px-3 py-2 text-xs font-medium text-zinc-700 transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
                        aria-label={`Ver detalle del pago ${payment.id}`}
                      >
                        Ver detalle
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}