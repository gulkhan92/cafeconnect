import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import type {
  AnalyticsRange,
  ConversionResponse,
  DashboardSummary,
  RevenueSummary,
  TableUtilizationResponse,
  TopItemsResponse,
} from "../types";

export interface RangeParams {
  range: AnalyticsRange;
  start?: string;
  end?: string;
}

function rangeIsReady(params: RangeParams): boolean {
  return params.range !== "custom" || Boolean(params.start && params.end);
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: async () => (await api.get<DashboardSummary>("/analytics/summary")).data,
    refetchInterval: 30_000,
  });
}

export function useRevenue(params: RangeParams) {
  return useQuery({
    queryKey: ["analytics", "revenue", params],
    queryFn: async () => (await api.get<RevenueSummary>("/analytics/revenue", { params })).data,
    enabled: rangeIsReady(params),
  });
}

export function useTopItems(params: RangeParams) {
  return useQuery({
    queryKey: ["analytics", "top-items", params],
    queryFn: async () => (await api.get<TopItemsResponse>("/analytics/top-items", { params })).data,
    enabled: rangeIsReady(params),
  });
}

export function useTableUtilization(params: RangeParams) {
  return useQuery({
    queryKey: ["analytics", "table-utilization", params],
    queryFn: async () => (await api.get<TableUtilizationResponse>("/analytics/table-utilization", { params })).data,
    enabled: rangeIsReady(params),
  });
}

export function useConversion(params: RangeParams) {
  return useQuery({
    queryKey: ["analytics", "conversion", params],
    queryFn: async () => (await api.get<ConversionResponse>("/analytics/conversion", { params })).data,
    enabled: rangeIsReady(params),
  });
}
