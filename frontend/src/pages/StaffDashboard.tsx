import { useState } from "react";

import { ConversionStats } from "../components/dashboard/ConversionStats";
import { DateRangeControl } from "../components/dashboard/DateRangeControl";
import { RecentActivityTable } from "../components/dashboard/RecentActivityTable";
import { RevenueChart } from "../components/dashboard/RevenueChart";
import { SummaryCards } from "../components/dashboard/SummaryCards";
import { TableUtilization } from "../components/dashboard/TableUtilization";
import { TopItemsChart } from "../components/dashboard/TopItemsChart";
import { Container } from "../components/ui/Container";
import { Section } from "../components/ui/Section";
import type { RangeParams } from "../hooks/useAnalytics";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export function StaffDashboard() {
  const [params, setParams] = useState<RangeParams>({ range: "today" });

  return (
    <Section className="pt-10">
      <Container>
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold text-cream-900">Staff dashboard</h1>
            <p className="mt-1 text-sm text-cream-600">
              Live business metrics — demo/seed orders are always excluded from every number here.
            </p>
          </div>
          <DateRangeControl
            value={params}
            onChange={(next) =>
              setParams(next.range === "custom" ? { range: "custom", start: next.start ?? todayIso(), end: next.end ?? todayIso() } : next)
            }
          />
        </div>

        <div className="mb-8">
          <SummaryCards />
        </div>

        <div className="mb-8 rounded-lg border border-cream-200 bg-cream-50 p-6 shadow-soft">
          <RevenueChart params={params} />
        </div>

        <div className="mb-8 grid gap-8 lg:grid-cols-2">
          <div className="rounded-lg border border-cream-200 bg-cream-50 p-6 shadow-soft">
            <TopItemsChart params={params} />
          </div>
          <div className="rounded-lg border border-cream-200 bg-cream-50 p-6 shadow-soft">
            <ConversionStats params={params} />
          </div>
        </div>

        <div className="mb-8 rounded-lg border border-cream-200 bg-cream-50 p-6 shadow-soft">
          <TableUtilization params={params} />
        </div>

        <div className="rounded-lg border border-cream-200 bg-cream-50 p-6 shadow-soft">
          <RecentActivityTable params={params} />
        </div>
      </Container>
    </Section>
  );
}
