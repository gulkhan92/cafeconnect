import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { RangeParams } from "../../hooks/useAnalytics";
import { useTopItems } from "../../hooks/useAnalytics";
import { Spinner } from "../ui/Spinner";

const PRIMARY = "#c15a2e";

export function TopItemsChart({ params }: { params: RangeParams }) {
  const [metric, setMetric] = useState<"quantity" | "revenue">("quantity");
  const { data, isLoading, isError } = useTopItems(params);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center gap-2 text-cream-600">
        <Spinner /> Loading top items…
      </div>
    );
  }

  if (isError || !data) {
    return <p className="text-error">Couldn't load top items.</p>;
  }

  const rows = metric === "quantity" ? data.by_quantity : data.by_revenue;
  const chartData = rows
    .map((row) => ({
      name: row.name,
      value: metric === "quantity" ? row.quantity_sold : Number(row.revenue),
    }))
    .reverse(); // Recharts renders bottom-up; reverse so #1 appears on top.

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-display text-lg font-semibold text-cream-900">Best sellers</h3>
        <div className="flex gap-1 rounded-md border border-cream-300 p-1">
          {(["quantity", "revenue"] as const).map((option) => (
            <button
              key={option}
              onClick={() => setMetric(option)}
              className={`rounded px-2.5 py-1 text-xs font-medium capitalize transition-colors ${
                metric === option ? "bg-primary-600 text-cream-50" : "text-cream-700 hover:bg-cream-100"
              }`}
            >
              By {option}
            </button>
          ))}
        </div>
      </div>

      {chartData.length === 0 ? (
        <p className="text-sm text-cream-600">No items sold in this range yet.</p>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 24, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#efe6d6" horizontal={false} />
            <XAxis type="number" tick={{ fill: "#7d6a4e", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis
              type="category"
              dataKey="name"
              width={140}
              tick={{ fill: "#3c3225", fontSize: 13 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={(value) => [
                metric === "revenue" ? `$${Number(value).toFixed(2)}` : String(value),
                metric === "revenue" ? "Revenue" : "Quantity sold",
              ]}
              contentStyle={{ borderRadius: 8, borderColor: "#e0d2b8" }}
            />
            <Bar dataKey="value" fill={PRIMARY} radius={[0, 4, 4, 0]} barSize={18} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
