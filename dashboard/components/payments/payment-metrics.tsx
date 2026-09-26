type PaymentMetricsProps = {
  total: number;
  paid: number;
  pending: number;
  failed: number;
  paidAmount: number;
  loading: boolean;
};

function formatAmount(
  amount: number,
): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

function MetricSkeleton() {
  return (
    <div
      className="h-8 w-24 animate-pulse rounded bg-zinc-200"
      aria-hidden="true"
    />
  );
}

export function PaymentMetrics({
  total,
  paid,
  pending,
  failed,
  paidAmount,
  loading,
}: PaymentMetricsProps) {
  const metrics = [
    {
      label: "Pagos visibles",
      value: total.toString(),
      description: "Registros en la consulta actual",
    },
    {
      label: "Pagados",
      value: paid.toString(),
      description: "Pagos completados",
    },
    {
      label: "Pendientes",
      value: pending.toString(),
      description: "Pendientes o procesando",
    },
    {
      label: "Fallidos",
      value: failed.toString(),
      description: "Pagos con estado fallido",
    },
    {
      label: "Monto pagado",
      value: `$${formatAmount(paidAmount)}`,
      description: "Total pagado en la consulta actual",
    },
  ];

  return (
    <section
      aria-label="Resumen de pagos"
      className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5"
    >
      {metrics.map((metric) => (
        <article
          key={metric.label}
          className="rounded-xl border border-zinc-200 bg-white p-5"
        >
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            {metric.label}
          </p>

          <div className="mt-3">
            {loading ? (
              <MetricSkeleton />
            ) : (
              <p className="text-2xl font-bold tracking-tight text-zinc-950">
                {metric.value}
              </p>
            )}
          </div>

          <p className="mt-2 text-xs leading-5 text-zinc-400">
            {metric.description}
          </p>
        </article>
      ))}
    </section>
  );
}