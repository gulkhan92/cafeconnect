import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { Booking, BookingSource } from "../types";

export function useMyBookings(enabled: boolean) {
  return useQuery({
    queryKey: ["my-bookings"],
    queryFn: async () => (await api.get<Booking[]>("/bookings/me")).data,
    enabled,
  });
}

export function useAllBookings(enabled: boolean) {
  return useQuery({
    queryKey: ["all-bookings"],
    queryFn: async () => (await api.get<Booking[]>("/bookings")).data,
    enabled,
  });
}

export function useCreateBooking() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { slot_id: string; party_size: number; created_via?: BookingSource }) =>
      (await api.post<Booking>("/bookings", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-bookings"] });
      queryClient.invalidateQueries({ queryKey: ["availability"] });
    },
  });
}
