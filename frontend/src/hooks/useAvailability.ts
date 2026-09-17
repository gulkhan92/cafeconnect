import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { TableAvailability } from "../types";

export function useAvailability(date: string, partySize: number, enabled: boolean) {
  return useQuery({
    queryKey: ["availability", date, partySize],
    queryFn: async () =>
      (await api.get<TableAvailability[]>("/tables/availability", { params: { date, party_size: partySize } })).data,
    enabled,
  });
}
