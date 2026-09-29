"use client";

import { useEffect } from "react";

interface DashboardErrorProps {
  error: Error & {
    digest?: string;
  };
  reset: () => void;
}

export default function DashboardError({
  error,
  reset,
}: DashboardErrorProps) {
  useEffect(() => {
    console.error(
      "Dashboard render error",
      error,
    );
  }, [error]);

  return (
    <main className="flex min-h-[60vh] items-center justify-center px-5 py-12">
      <section
        className="w-full max-w-xl rounded-2xl border border-red-200 bg-white p-8 text-center shadow-sm"
        role="alert"
        aria-live="assertive"
      >
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-red-500">
          Error inesperado
        </p>

        <h1 className="mt-3 text-2xl font-bold tracking-tight text-zinc-950">
          No pudimos mostrar esta sección
        </h1>

        <p className="mt-3 text-sm leading-6 text-zinc-500">
          Ocurrió un problema inesperado en el dashboard.
          Puedes intentar cargar esta sección nuevamente.
        </p>

        <button
          type="button"
          onClick={reset}
          className="mt-6 min-h-11 rounded-lg bg-zinc-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2"
        >
          Intentar nuevamente
        </button>
      </section>
    </main>
  );
}
