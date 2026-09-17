import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { RangeParams } from "../../hooks/useAnalytics";
import { useRevenue } from "../../hooks/useAnalytics";
import { Spinner } from "../ui/Spinner";

const PRIMARY = "#c15a2e";

function formatShortDate(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function RevenueChart({ params }: { params: RangeParams }) {
  const { data, isLoading, isError } = useRevenue(params);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center gap-2 text-cream-600">
        <Spinner /> Loading revenue…
      </div>
    );
  }

  if (isError || !data) {
    return <p className="text-error">Couldn't load revenue data.</p>;
  }

  const chartData = data.series.map((point) => ({ date: point.date, revenue: Number(point.revenue) }));

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-baseline gap-x-6 gap-y-1">
        <div>
          <p className="text-sm text-cream-600">Total revenue</p>
          <p className="font-display text-2xl font-semibold text-cream-900">${data.total_revenue}</p>
        </div>
        <div>
          <p className="text-sm text-cream-600">Orders</p>
          <p className="font-display text-2xl font-semibold text-cream-900">{data.order_count}</p>
        </div>
        <div>
          <p className="text-sm text-cream-600">Avg. order value</p>
          <p className="font-display text-2xl font-semibold text-cream-900">${data.average_order_value}</p>
        </div>
      </div>

      {chartData.length === 0 ? (
        <p className="text-sm text-cream-600">No revenue in this range yet.</p>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={PRIMARY} stopOpacity={0.35} />
                <stop offset="100%" stopColor={PRIMARY} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#efe6d6" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatShortDate}
              tick={{ fill: "#7d6a4e", fontSize: 12 }}
              axisLine={{ stroke: "#e0d2b8" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#7d6a4e", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `$${v}`}
              width={56}
            />
            <Tooltip
              formatter={(value) => [`$${Number(value).toFixed(2)}`, "Revenue"]}
              labelFormatter={(label) => formatShortDate(String(label))}
              contentStyle={{ borderRadius: 8, borderColor: "#e0d2b8" }}
            />
            <Area type="monotone" dataKey="revenue" stroke={PRIMARY} strokeWidth={2} fill="url(#revenueFill)" />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
