import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { MenuItem } from "../types";

export interface CartLine {
  menuItemId: string;
  name: string;
  price: string;
  quantity: number;
}

interface CartState {
  lines: CartLine[];
  addItem: (item: MenuItem, quantity?: number) => void;
  removeItem: (menuItemId: string) => void;
  setQuantity: (menuItemId: string, quantity: number) => void;
  clear: () => void;
  totalCents: () => number;
  totalCount: () => number;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      lines: [],

      addItem: (item, quantity = 1) =>
        set((state) => {
          const existing = state.lines.find((line) => line.menuItemId === item.id);
          if (existing) {
            return {
              lines: state.lines.map((line) =>
                line.menuItemId === item.id ? { ...line, quantity: line.quantity + quantity } : line,
              ),
            };
          }
          return {
            lines: [...state.lines, { menuItemId: item.id, name: item.name, price: item.price, quantity }],
          };
        }),

      removeItem: (menuItemId) => set((state) => ({ lines: state.lines.filter((l) => l.menuItemId !== menuItemId) })),

      setQuantity: (menuItemId, quantity) =>
        set((state) => ({
          lines:
            quantity <= 0
              ? state.lines.filter((l) => l.menuItemId !== menuItemId)
              : state.lines.map((l) => (l.menuItemId === menuItemId ? { ...l, quantity } : l)),
        })),

      clear: () => set({ lines: [] }),

      totalCents: () =>
        Math.round(get().lines.reduce((sum, line) => sum + Number(line.price) * line.quantity, 0) * 100),

      totalCount: () => get().lines.reduce((sum, line) => sum + line.quantity, 0),
    }),
    { name: "cafeconnect-cart" },
  ),
);
