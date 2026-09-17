import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import type { MenuCategory, MenuSearchResult } from "../types";

export function useMenu() {
  return useQuery({
    queryKey: ["menu"],
    queryFn: async () => (await api.get<MenuCategory[]>("/menu")).data,
  });
}

export function useMenuSearch(query: string) {
  return useQuery({
    queryKey: ["menu-search", query],
    queryFn: async () => (await api.get<MenuSearchResult[]>("/menu/search", { params: { q: query } })).data,
    enabled: query.trim().length > 1,
  });
}
