type OrderMetricsProps = {
  total: number;
  created: number;
  confirmed: number;
  submitted: number;
  loading: boolean;
};

type MetricCardProps = {
  label: string;
  value: number;
  loading: boolean;
};

function MetricCard({
  label,
  value,
  loading,
}: MetricCardProps) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5">
      <p className="text-sm text-zinc-500">{label}</p>

      <p className="mt-2 text-3xl font-bold">
        {loading ? "-" : value}
      </p>
    </div>
  );
}

export function OrderMetrics({
  total,
  created,
  confirmed,
  submitted,
  loading,
}: OrderMetricsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <MetricCard
        label="Todos"
        value={total}
        loading={loading}
      />

      <MetricCard
        label="Nuevos"
        value={created}
        loading={loading}
      />

      <MetricCard
        label="Confirmados"
        value={confirmed}
        loading={loading}
      />

      <MetricCard
        label="Enviados"
        value={submitted}
        loading={loading}
      />
    </div>
  );
}