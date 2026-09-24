type DashboardStateVariant = "loading" | "error" | "empty";

type DashboardStateProps = {
  variant: DashboardStateVariant;
  title: string;
  description?: string;
};

const titleClasses: Record<DashboardStateVariant, string> = {
  loading: "text-zinc-600",
  error: "text-red-600",
  empty: "text-zinc-600",
};

export function DashboardState({
  variant,
  title,
  description,
}: DashboardStateProps) {
  return (
    <div
      className="flex min-h-48 items-center justify-center px-5 py-12"
      role={variant === "error" ? "alert" : "status"}
      aria-live={variant === "error" ? "assertive" : "polite"}
    >
      <div className="max-w-xl text-center">
        {variant === "loading" && (
          <div
            className="mx-auto mb-4 h-5 w-5 animate-spin rounded-full border-2 border-zinc-200 border-t-zinc-700"
            aria-hidden="true"
          />
        )}

        <p className={`text-sm font-medium ${titleClasses[variant]}`}>
          {title}
        </p>

        {description && (
          <p className="mt-2 text-xs leading-5 text-zinc-400">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}