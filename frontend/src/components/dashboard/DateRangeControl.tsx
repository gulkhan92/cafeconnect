import type { AnalyticsRange } from "../../types";
import type { RangeParams } from "../../hooks/useAnalytics";

const OPTIONS: { value: AnalyticsRange; label: string }[] = [
  { value: "today", label: "Today" },
  { value: "week", label: "This week" },
  { value: "month", label: "This month" },
  { value: "custom", label: "Custom" },
];

interface Props {
  value: RangeParams;
  onChange: (next: RangeParams) => void;
}

export function DateRangeControl({ value, onChange }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex gap-1 rounded-md border border-cream-300 bg-cream-50 p-1">
        {OPTIONS.map((option) => (
          <button
            key={option.value}
            onClick={() => onChange({ range: option.value, start: value.start, end: value.end })}
            className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
              value.range === option.value ? "bg-primary-600 text-cream-50" : "text-cream-700 hover:bg-cream-100"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {value.range === "custom" && (
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={value.start ?? ""}
            onChange={(e) => onChange({ ...value, start: e.target.value })}
            className="rounded-md border border-cream-300 bg-cream-50 px-2.5 py-1.5 text-sm outline-none focus:border-primary-400"
            aria-label="Start date"
          />
          <span className="text-cream-500">to</span>
          <input
            type="date"
            value={value.end ?? ""}
            onChange={(e) => onChange({ ...value, end: e.target.value })}
            className="rounded-md border border-cream-300 bg-cream-50 px-2.5 py-1.5 text-sm outline-none focus:border-primary-400"
            aria-label="End date"
          />
        </div>
      )}
    </div>
  );
}
