import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ApiUser, ApiNotification, DashboardStats, ApiWell, ApiReport } from "./api";

// ── Auth Store ────────────────────────────────────────────────────────────────

interface AuthState {
  token: string | null;
  user: ApiUser | null;
  setAuth: (token: string, user: ApiUser) => void;
  clearAuth: () => void;
  updateUser: (user: ApiUser) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => {
        localStorage.setItem("munai_token", token);
        localStorage.setItem("munai_user", JSON.stringify(user));
        set({ token, user });
      },
      clearAuth: () => {
        localStorage.removeItem("munai_token");
        localStorage.removeItem("munai_user");
        set({ token: null, user: null });
      },
      updateUser: (user) => set({ user }),
    }),
    { name: "munai-auth", partialize: (s) => ({ token: s.token, user: s.user }) }
  )
);

// ── Notifications Store ───────────────────────────────────────────────────────

interface NotifState {
  notifications: ApiNotification[];
  setNotifications: (n: ApiNotification[]) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  unreadCount: () => number;
}

export const useNotifStore = create<NotifState>((set, get) => ({
  notifications: [],
  setNotifications: (notifications) => set({ notifications }),
  markRead: (id) =>
    set((s) => ({
      notifications: s.notifications.map((n) => n.id === id ? { ...n, unread: false } : n),
    })),
  markAllRead: () =>
    set((s) => ({ notifications: s.notifications.map((n) => ({ ...n, unread: false })) })),
  unreadCount: () => get().notifications.filter((n) => n.unread).length,
}));

// ── Dashboard Store ───────────────────────────────────────────────────────────

interface DashboardState {
  stats: DashboardStats | null;
  setStats: (s: DashboardStats) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  stats: null,
  setStats: (stats) => set({ stats }),
}));

// ── Wells Store ───────────────────────────────────────────────────────────────

interface WellsState {
  wells: ApiWell[];
  setWells: (w: ApiWell[]) => void;
  updateWell: (id: string, data: Partial<ApiWell>) => void;
  removeWell: (id: string) => void;
}

export const useWellsStore = create<WellsState>((set) => ({
  wells: [],
  setWells: (wells) => set({ wells }),
  updateWell: (id, data) =>
    set((s) => ({ wells: s.wells.map((w) => w.id === id ? { ...w, ...data } : w) })),
  removeWell: (id) => set((s) => ({ wells: s.wells.filter((w) => w.id !== id) })),
}));

// ── Reports Store ─────────────────────────────────────────────────────────────

interface ReportsState {
  reports: ApiReport[];
  setReports: (r: ApiReport[]) => void;
  updateReport: (id: string, data: Partial<ApiReport>) => void;
  removeReport: (id: string) => void;
}

export const useReportsStore = create<ReportsState>((set) => ({
  reports: [],
  setReports: (reports) => set({ reports }),
  updateReport: (id, data) =>
    set((s) => ({ reports: s.reports.map((r) => r.id === id ? { ...r, ...data } : r) })),
  removeReport: (id) => set((s) => ({ reports: s.reports.filter((r) => r.id !== id) })),
}));
