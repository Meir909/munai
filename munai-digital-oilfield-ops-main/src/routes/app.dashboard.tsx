import { createFileRoute, Link } from "@tanstack/react-router";
import { useSession } from "@/lib/session";
import { Droplets, AlertTriangle, FileText, TrendingUp, Sparkles, Mic, Plus, Users, ShieldCheck, BarChart3, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, BarChart, Bar, CartesianGrid } from "recharts";
import { StatusBadge } from "@/components/status-badge";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi, reportsApi, notificationsApi } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { ru } from "date-fns/locale";

export const Route = createFileRoute("/app/dashboard")({
  head: () => ({ meta: [{ title: "Панель управления — MUNAI" }] }),
  component: Dashboard,
});

function Dashboard() {
  const { role, user } = useSession();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: dashboardApi.stats,
    refetchInterval: 60000,
  });

  const { data: reports = [] } = useQuery({
    queryKey: ["reports"],
    queryFn: () => reportsApi.list(),
    refetchInterval: 30000,
  });

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: notificationsApi.list,
    refetchInterval: 30000,
  });

  const activeWells = stats?.active_wells ?? 0;
  const warningWells = stats?.warning_wells ?? 0;
  const pendingReports = stats?.pending_reports ?? 0;
  const flagged = stats?.flagged_reports ?? 0;
  const productionTrend = stats?.production_trend ?? [];
  const wellStatuses = stats?.well_statuses ?? [];
  const totalProduction = stats?.total_production ?? 0;

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-sm text-muted-foreground">Здравствуйте, {user.name.split(" ")[0]} 👋</div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight mt-1">
            {role === "operator" && "Ваши скважины и отчёты"}
            {role === "manager" && "Контроль участка"}
            {role === "director" && "Сводка по добыче"}
            {role === "admin" && "Системная панель"}
          </h1>
          <div className="text-sm text-muted-foreground mt-1">{user.region} · {user.position}</div>
        </div>
        {role === "operator" && (
          <Link to="/app/reports/new">
            <Button size="lg" className="h-12 px-6 gap-2"><Plus className="h-5 w-5" /> Новый отчёт</Button>
          </Link>
        )}
        {role === "director" && (
          <Link to="/app/approvals">
            <Button size="lg" className="h-12 px-6 gap-2"><ShieldCheck className="h-5 w-5" /> Согласовать</Button>
          </Link>
        )}
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Droplets} label="Активные скважины" value={activeWells} trend="+3 за неделю" tone="info" />
        <StatCard icon={AlertTriangle} label="Требуют внимания" value={warningWells} trend="−1 за день" tone="warning" />
        <StatCard icon={FileText} label="На согласовании" value={pendingReports} trend={`${flagged} с аномалией`} tone="primary" />
        <StatCard icon={TrendingUp} label="Добыча за неделю" value={`${totalProduction.toFixed(0)} м³`} trend="+8.4%" tone="success" />
      </div>

      {/* Quick actions — operator only */}
      {role === "operator" && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <QuickAction to="/app/reports/new" icon={Plus} label="Новый отчёт" sub="Создать вручную" />
          <QuickAction to="/app/reports/new" icon={Mic} label="Голосовой ввод" sub="Просто продиктуйте" />
          <QuickAction to="/app/map" icon={Droplets} label="Карта скважин" sub="Посмотреть статусы" />
          <QuickAction to="/app/ai" icon={Sparkles} label="AI-помощник" sub="Задать вопрос" />
        </div>
      )}

      {/* Charts row */}
      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 rounded-2xl border border-border bg-card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold">Добыча за неделю</h3>
              <p className="text-xs text-muted-foreground">Нефть и газ, м³/сутки</p>
            </div>
            <BarChart3 className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={productionTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
                <XAxis dataKey="day" tickLine={false} axisLine={false} fontSize={12} />
                <YAxis tickLine={false} axisLine={false} fontSize={12} />
                <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid var(--color-border)", background: "var(--color-card)" }} />
                <Line type="monotone" dataKey="oil" stroke="var(--color-primary)" strokeWidth={3} dot={{ r: 4 }} name="Нефть" />
                <Line type="monotone" dataKey="gas" stroke="var(--color-info)" strokeWidth={2} dot={{ r: 3 }} name="Газ" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Статусы скважин</h3>
            <Link to="/app/wells" className="text-xs text-primary hover:underline">Все</Link>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={wellStatuses}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
                <XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={11} />
                <YAxis tickLine={false} axisLine={false} fontSize={11} />
                <Tooltip />
                <Bar dataKey="v" fill="var(--color-primary)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent reports & notifications */}
      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 rounded-2xl border border-border bg-card">
          <div className="flex items-center justify-between p-5 border-b border-border">
            <h3 className="font-semibold">Последние отчёты</h3>
            <Link to="/app/reports" className="text-xs text-primary hover:underline">Все отчёты</Link>
          </div>
          <div className="divide-y divide-border">
            {reports.slice(0, 5).map((r) => (
              <div key={r.id} className="p-4 flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-accent grid place-items-center text-xs font-bold text-accent-foreground">{r.well_code?.split("-")[1]}</div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm truncate">{r.well_code} · {r.summary}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {r.operator_name} · {formatDistanceToNow(new Date(r.created_at), { addSuffix: true, locale: ru })}
                  </div>
                </div>
                <StatusBadge status={r.status} />
                <div className="hidden md:flex items-center gap-1 text-xs text-muted-foreground">
                  <Sparkles className="h-3.5 w-3.5 text-primary" /> AI {r.ai_score}
                </div>
              </div>
            ))}
            {reports.length === 0 && (
              <div className="p-8 text-center text-sm text-muted-foreground">Нет отчётов</div>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card">
          <div className="flex items-center justify-between p-5 border-b border-border">
            <h3 className="font-semibold">Уведомления</h3>
            <Link to="/app/notifications" className="text-xs text-primary hover:underline">Все</Link>
          </div>
          <div className="divide-y divide-border">
            {notifications.slice(0, 4).map((n) => (
              <div key={n.id} className="p-4">
                <div className="flex items-start gap-2">
                  <span className={`mt-1.5 h-2 w-2 rounded-full ${n.tone === "warning" ? "bg-warning" : n.tone === "success" ? "bg-success" : n.tone === "destructive" ? "bg-destructive" : "bg-info"}`} />
                  <div className="flex-1">
                    <div className="font-medium text-sm">{n.title}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">{n.body}</div>
                    <div className="text-[11px] text-muted-foreground mt-1">
                      {formatDistanceToNow(new Date(n.created_at), { addSuffix: true, locale: ru })}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {notifications.length === 0 && (
              <div className="p-8 text-center text-sm text-muted-foreground">Нет уведомлений</div>
            )}
          </div>
        </div>
      </div>

      {/* Role-specific blocks */}
      {(role === "manager" || role === "director") && (
        <div className="grid md:grid-cols-3 gap-4">
          <RoleCard icon={Users} title="Команда" value="Управление" to="/app/admin" />
          <RoleCard icon={ShieldCheck} title="На согласовании" value={`${pendingReports} отчётов`} to="/app/approvals" />
          <RoleCard icon={Sparkles} title="AI-аномалий" value={`${flagged} обнаружено`} to="/app/ai" />
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, trend, tone }: { icon: React.ElementType; label: string; value: React.ReactNode; trend: string; tone: "info" | "warning" | "primary" | "success" }) {
  const toneCls = {
    info: "bg-info/10 text-info",
    warning: "bg-warning/15 text-warning-foreground",
    primary: "bg-primary/10 text-primary",
    success: "bg-success/10 text-success",
  }[tone];
  return (
    <div className="rounded-2xl border border-border bg-card p-5">
      <div className={`h-10 w-10 rounded-xl grid place-items-center ${toneCls}`}><Icon className="h-5 w-5" /></div>
      <div className="mt-3 text-3xl font-bold tracking-tight">{value}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
      <div className="text-xs mt-1 text-muted-foreground">{trend}</div>
    </div>
  );
}

function QuickAction({ to, icon: Icon, label, sub }: { to: string; icon: React.ElementType; label: string; sub: string }) {
  return (
    <Link to={to} className="group rounded-2xl border border-border bg-card p-5 hover:border-primary hover:shadow-elevated transition flex items-center gap-4">
      <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary grid place-items-center group-hover:bg-primary group-hover:text-primary-foreground transition">
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <div className="font-semibold">{label}</div>
        <div className="text-xs text-muted-foreground">{sub}</div>
      </div>
    </Link>
  );
}

function RoleCard({ icon: Icon, title, value, to }: { icon: React.ElementType; title: string; value: string; to: string }) {
  return (
    <Link to={to} className="rounded-2xl border border-border bg-card p-5 hover:border-primary transition flex items-center gap-4">
      <div className="h-12 w-12 rounded-xl bg-accent grid place-items-center text-primary"><Icon className="h-6 w-6" /></div>
      <div>
        <div className="text-sm text-muted-foreground">{title}</div>
        <div className="text-lg font-semibold">{value}</div>
      </div>
    </Link>
  );
}
