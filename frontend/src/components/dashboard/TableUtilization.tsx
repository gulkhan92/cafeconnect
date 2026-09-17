import type { RangeParams } from "../../hooks/useAnalytics";
import { useTableUtilization } from "../../hooks/useAnalytics";
import { Spinner } from "../ui/Spinner";

function intensity(ratio: number): string {
  // Sequential, single-hue (primary) intensity scale rather than a rainbow.
  const clamped = Math.max(0, Math.min(1, ratio));
  return `rgba(193, 90, 46, ${0.15 + clamped * 0.75})`;
}

export function TableUtilization({ params }: { params: RangeParams }) {
  const { data, isLoading, isError } = useTableUtilization(params);

  if (isLoading) {
    return (
      <div className="flex h-48 items-center justify-center gap-2 text-cream-600">
        <Spinner /> Loading table utilization…
      </div>
    );
  }

  if (isError || !data) {
    return <p className="text-error">Couldn't load table utilization.</p>;
  }

  const maxHourCount = Math.max(1, ...data.peak_hours.map((h) => h.booking_count));
  const hours = Array.from({ length: 24 }, (_, hour) => {
    const match = data.peak_hours.find((h) => h.hour === hour);
    return { hour, count: match?.booking_count ?? 0 };
  }).filter((h) => h.count > 0 || (h.hour >= 7 && h.hour <= 22));

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <div>
        <h3 className="mb-4 font-display text-lg font-semibold text-cream-900">Peak hours</h3>
        {data.peak_hours.length === 0 ? (
          <p className="text-sm text-cream-600">No bookings in this range yet.</p>
        ) : (
          <div className="flex items-end gap-1 overflow-x-auto pb-1" role="img" aria-label="Bookings by hour of day">
            {hours.map(({ hour, count }) => (
              <div key={hour} className="flex flex-1 min-w-6 flex-col items-center gap-1">
                <div
                  title={`${hour}:00 — ${count} booking${count === 1 ? "" : "s"}`}
                  className="w-full rounded-t"
                  style={{
                    height: `${8 + (count / maxHourCount) * 90}px`,
                    backgroundColor: intensity(count / maxHourCount),
                  }}
                />
                <span className="text-[10px] text-cream-500">{hour}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h3 className="mb-4 font-display text-lg font-semibold text-cream-900">Occupancy by table</h3>
        {data.tables.length === 0 ? (
          <p className="text-sm text-cream-600">No tables found.</p>
        ) : (
          <div className="space-y-2">
            {data.tables.map((table) => (
              <div key={table.table_id} className="flex items-center gap-3">
                <span className="w-16 shrink-0 text-sm font-medium text-cream-800">{table.table_number}</span>
                <div className="h-4 flex-1 overflow-hidden rounded-full bg-cream-200">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${table.occupancy_rate * 100}%`,
                      backgroundColor: intensity(table.occupancy_rate),
                    }}
                  />
                </div>
                <span className="w-20 shrink-0 text-right text-sm text-cream-600">
                  {Math.round(table.occupancy_rate * 100)}% ({table.booked_slots}/{table.total_slots})
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
