import { createFileRoute } from "@tanstack/react-router";
import { Area, AreaChart, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar } from "recharts";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/app/kpi")({
  head: () => ({ meta: [{ title: "KPI — MUNAI" }] }),
  component: KpiPage,
});

function KpiPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: dashboardApi.stats,
    refetchInterval: 60000,
  });

  const productionTrend = stats?.production_trend ?? [];

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-5">
      <div>
        <h1 className="text-3xl md:text-4xl font-bold">KPI и эффективность</h1>
        <p className="text-sm text-muted-foreground mt-1">Показатели по региону Мангистау</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { l: "Выполнение плана", v: "104%", s: "+4% к плану", t: "text-success" },
          { l: "Эффективность скважин", v: `${stats ? Math.round((stats.active_wells / (stats.active_wells + stats.warning_wells + 4 || 1)) * 100) : 87}%`, s: "+3% за месяц", t: "text-success" },
          { l: "На согласовании", v: `${stats?.pending_reports ?? 0}`, s: `${stats?.flagged_reports ?? 0} с аномалией`, t: stats?.flagged_reports ? "text-warning-foreground" : "text-success" },
          { l: "Добыча за неделю", v: `${stats ? Math.round(stats.total_production) : 0} м³`, s: "+8.4%", t: "text-success" },
        ].map((k) => (
          <div key={k.l} className="rounded-2xl border border-border bg-card p-5">
            <div className="text-sm text-muted-foreground">{k.l}</div>
            <div className="mt-2 text-3xl font-bold">
              {isLoading ? <Loader2 className="h-6 w-6 animate-spin text-primary" /> : k.v}
            </div>
            <div className={`text-xs mt-1 ${k.t}`}>{k.s}</div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        <Chart title="Тренд добычи нефти" subtitle="м³ / сутки">
          <AreaChart data={productionTrend}>
            <defs>
              <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.4} />
                <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" opacity={0.5} />
            <XAxis dataKey="day" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip />
            <Area dataKey="oil" stroke="var(--color-primary)" strokeWidth={2.5} fill="url(#g)" name="Нефть" />
          </AreaChart>
        </Chart>
        <Chart title="Статусы скважин" subtitle="Количество по статусу">
          <BarChart data={stats?.well_statuses ?? []}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.5} />
            <XAxis dataKey="name" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis fontSize={11} tickLine={false} axisLine={false} />
            <Tooltip />
            <Bar dataKey="v" fill="var(--color-primary)" radius={[8, 8, 0, 0]} />
          </BarChart>
        </Chart>
      </div>
    </div>
  );
}

function Chart({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactElement }) {
  return (
    <div className="rounded-2xl border border-border bg-card p-5">
      <div className="mb-4">
        <h3 className="font-semibold">{title}</h3>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </div>
      <div className="h-64"><ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer></div>
    </div>
  );
}
