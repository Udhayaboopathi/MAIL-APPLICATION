import { create } from "zustand";
import type { StateCreator } from "zustand";
import { persist } from "zustand/middleware";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  email: string | null;
  role: string | null;
  setSession: (session: {
    accessToken: string;
    refreshToken: string;
    email?: string;
    role?: string;
  }) => void;
  clearSession: () => void;
};

const authStoreCreator: StateCreator<AuthState> = (set) => ({
  accessToken: null,
  refreshToken: null,
  email: null,
  role: null,
  setSession: (session) =>
    set({
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      email: session.email ?? null,
      role: session.role ?? null,
    }),
  clearSession: () =>
    set({ accessToken: null, refreshToken: null, email: null, role: null }),
});

export const useAuthStore = create<AuthState>()(
  persist(authStoreCreator, { name: "nexudo-auth" }),
);
