// Central API service — all requests go through here.
const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

function getToken(): string | null {
  return localStorage.getItem("munai_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem("munai_token");
    localStorage.removeItem("munai_user");
    window.location.href = "/login";
    throw new Error("Сессия истекла. Войдите снова.");
  }

  if (!res.ok) {
    let msg = `Ошибка ${res.status}`;
    try {
      const data = await res.json();
      msg = data.detail ?? msg;
    } catch {}
    throw new Error(msg);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

const get = <T>(path: string) => request<T>(path);
const post = <T>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) });
const put = <T>(path: string, body: unknown) => request<T>(path, { method: "PUT", body: JSON.stringify(body) });
const del = <T>(path: string) => request<T>(path, { method: "DELETE" });

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ApiUser {
  id: string;
  name: string;
  email: string;
  role: "operator" | "manager" | "director" | "admin";
  position: string;
  region: string;
  active: boolean;
}

export interface ApiWell {
  id: string;
  code: string;
  name: string;
  status: "active" | "warning" | "inactive" | "broken";
  product: "oil" | "gas" | "condensate";
  production24h: number;
  temperature: number;
  tubing_internal_p: number;
  tubing_external_p: number;
  annulus_p: number;
  pump_strokes: number;
  lat: number;
  lng: number;
  operator_id: string | null;
  manager_id: string | null;
  operator_name: string | null;
  manager_name: string | null;
  last_report: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiReport {
  id: string;
  well_id: string;
  well_code: string | null;
  well_name: string | null;
  operator_id: string;
  operator_name: string | null;
  status: "pending" | "approved" | "flagged" | "rejected";
  ai_score: number;
  summary: string;
  flag: string | null;
  temperature: number | null;
  production24h: number | null;
  tubing_internal_p: number | null;
  tubing_external_p: number | null;
  annulus_p: number | null;
  pump_strokes: number | null;
  comment: string | null;
  created_at: string;
  reviewed_at: string | null;
}

export interface ApiNotification {
  id: string;
  icon: string;
  title: string;
  body: string;
  tone: "warning" | "success" | "info" | "destructive";
  unread: boolean;
  created_at: string;
}

export interface ApiCalendarEvent {
  id: string;
  title: string;
  date: string;
  event_type: string;
  created_by: string | null;
}

export interface ApiAuditLog {
  id: string;
  who: string;
  action: string;
  target: string;
  created_at: string;
}

export interface DashboardStats {
  active_wells: number;
  warning_wells: number;
  pending_reports: number;
  flagged_reports: number;
  total_production: number;
  production_trend: Array<{ day: string; oil: number; gas: number }>;
  well_statuses: Array<{ name: string; v: number }>;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: ApiUser;
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    post<TokenResponse>("/auth/login", { email, password }),
  register: (name: string, email: string, password: string, role?: string, position?: string, region?: string) =>
    post<TokenResponse>("/auth/register", { name, email, password, role, position, region }),
  me: () => get<ApiUser>("/auth/me"),
};

// ── Dashboard ─────────────────────────────────────────────────────────────────

export const dashboardApi = {
  stats: () => get<DashboardStats>("/dashboard/stats"),
};

// ── Wells ─────────────────────────────────────────────────────────────────────

export const wellsApi = {
  list: (q?: string, status?: string) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (status && status !== "all") params.set("status", status);
    const qs = params.toString();
    return get<ApiWell[]>(`/wells${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => get<ApiWell>(`/wells/${id}`),
  create: (body: Partial<ApiWell>) => post<ApiWell>("/wells", body),
  update: (id: string, body: Partial<ApiWell>) => put<ApiWell>(`/wells/${id}`, body),
  delete: (id: string) => del<{ ok: boolean }>(`/wells/${id}`),
};

// ── Reports ───────────────────────────────────────────────────────────────────

export const reportsApi = {
  list: (q?: string, status?: string) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (status && status !== "all") params.set("status", status);
    const qs = params.toString();
    return get<ApiReport[]>(`/reports${qs ? `?${qs}` : ""}`);
  },
  pending: () => get<ApiReport[]>("/reports/pending"),
  get: (id: string) => get<ApiReport>(`/reports/${id}`),
  create: (body: {
    well_id: string;
    temperature?: number;
    production24h?: number;
    tubing_internal_p?: number;
    tubing_external_p?: number;
    annulus_p?: number;
    pump_strokes?: number;
    comment?: string;
  }) => post<ApiReport>("/reports", body),
  review: (id: string, status: "approved" | "rejected", comment?: string) =>
    post<ApiReport>(`/reports/${id}/review`, { status, comment }),
  delete: (id: string) => del<{ ok: boolean }>(`/reports/${id}`),
};

// ── Users ─────────────────────────────────────────────────────────────────────

export const usersApi = {
  list: () => get<ApiUser[]>("/users"),
  create: (body: { name: string; email: string; password: string; role: string; position?: string; region?: string }) =>
    post<ApiUser>("/users", body),
  update: (id: string, body: Partial<ApiUser & { password: string }>) => put<ApiUser>(`/users/${id}`, body),
  delete: (id: string) => del<{ ok: boolean }>(`/users/${id}`),
};

// ── Notifications ─────────────────────────────────────────────────────────────

export const notificationsApi = {
  list: () => get<ApiNotification[]>("/notifications"),
  markRead: (id: string) => post<{ ok: boolean }>(`/notifications/${id}/read`, {}),
  markAllRead: () => post<{ ok: boolean }>("/notifications/read-all", {}),
};

// ── Calendar ──────────────────────────────────────────────────────────────────

export const calendarApi = {
  list: () => get<ApiCalendarEvent[]>("/calendar"),
  create: (body: { title: string; date: string; event_type: string }) =>
    post<ApiCalendarEvent>("/calendar", body),
  delete: (id: string) => del<{ ok: boolean }>(`/calendar/${id}`),
};

// ── Audit ─────────────────────────────────────────────────────────────────────

export const auditApi = {
  list: () => get<ApiAuditLog[]>("/audit"),
};

// ── AI ────────────────────────────────────────────────────────────────────────

export const aiApi = {
  chat: (message: string) => post<{ reply: string; suggestions: string[] }>("/ai/chat", { message }),
  insights: () => get<{ insights: unknown[]; suggestions: string[] }>("/ai/insights"),
};
