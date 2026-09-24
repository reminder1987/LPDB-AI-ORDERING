export function formatCurrency(value: number | null) {
  if (value === null) {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export function formatStatus(status: string) {
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
