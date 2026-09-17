import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { Order } from "../types";

export function useMyOrders(enabled: boolean) {
  return useQuery({
    queryKey: ["my-orders"],
    queryFn: async () => (await api.get<Order[]>("/orders/me")).data,
    enabled,
    refetchInterval: enabled ? 15_000 : false, // simple live-status polling
  });
}

export function useAllOrders(params: { date_from?: string; date_to?: string }, enabled: boolean) {
  return useQuery({
    queryKey: ["all-orders", params],
    queryFn: async () => (await api.get<Order[]>("/orders", { params })).data,
    enabled,
  });
}

export function useCreateOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { items: { menu_item_id: string; quantity: number }[]; booking_id?: string }) =>
      (await api.post<Order>("/orders", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-orders"] });
    },
  });
}
