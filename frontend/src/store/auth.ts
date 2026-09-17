import { create } from "zustand";
import { persist } from "zustand/middleware";

import { api } from "../lib/api";
import type { User } from "../types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isHydrating: boolean;
  setTokens: (accessToken: string, refreshToken: string) => void;
  clearSession: () => void;
  login: (email: string, password: string) => Promise<User>;
  register: (name: string, email: string, password: string, phone?: string) => Promise<void>;
  logout: () => Promise<void>;
  hydrate: () => Promise<void>;
}

// The access token deliberately lives only in memory (per the plan's auth
// design) and is never persisted; only the refresh token + user survive a
// reload, and hydrate() exchanges the refresh token for a fresh access token
// on app boot.
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isHydrating: true,

      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),

      clearSession: () => set({ accessToken: null, refreshToken: null, user: null }),

      login: async (email, password) => {
        const { data } = await api.post("/auth/login", { email, password });
        set({ accessToken: data.access_token, refreshToken: data.refresh_token });
        const me = await api.get<User>("/users/me");
        set({ user: me.data });
        return me.data;
      },

      register: async (name, email, password, phone) => {
        await api.post("/auth/register", { name, email, password, phone: phone || undefined });
      },

      logout: async () => {
        const refreshToken = get().refreshToken;
        if (refreshToken) {
          try {
            await api.post("/auth/logout", { refresh_token: refreshToken });
          } catch {
            // best-effort revoke; clear local session regardless
          }
        }
        set({ accessToken: null, refreshToken: null, user: null });
      },

      hydrate: async () => {
        const refreshToken = get().refreshToken;
        if (!refreshToken) {
          set({ isHydrating: false });
          return;
        }
        try {
          const { data } = await api.post("/auth/refresh", { refresh_token: refreshToken });
          set({ accessToken: data.access_token, refreshToken: data.refresh_token });
          const me = await api.get<User>("/users/me");
          set({ user: me.data });
        } catch {
          set({ accessToken: null, refreshToken: null, user: null });
        } finally {
          set({ isHydrating: false });
        }
      },
    }),
    {
      name: "cafeconnect-auth",
      partialize: (state) => ({ refreshToken: state.refreshToken }),
    },
  ),
);
