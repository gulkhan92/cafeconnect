import { useDashboardSummary } from "../../hooks/useAnalytics";
import { Spinner } from "../ui/Spinner";

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-cream-200 bg-cream-50 p-5 shadow-soft">
      <p className="text-sm text-cream-600">{label}</p>
      <p className="mt-1 font-display text-3xl font-semibold text-cream-900">{value}</p>
    </div>
  );
}

export function SummaryCards() {
  const { data, isLoading, isError } = useDashboardSummary();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-cream-600">
        <Spinner /> Loading today's numbers…
      </div>
    );
  }

  if (isError || !data) {
    return <p className="text-error">Couldn't load today's summary.</p>;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <Card label="Today's revenue" value={`$${data.today_revenue}`} />
      <Card label="Today's bookings" value={String(data.today_bookings)} />
      <Card label="Active orders" value={String(data.active_orders)} />
    </div>
  );
}
