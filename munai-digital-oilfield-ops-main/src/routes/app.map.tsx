import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { wellsApi, type ApiWell } from "@/lib/api";
import { Loader2, Plus } from "lucide-react";

export const Route = createFileRoute("/app/map")({
  head: () => ({ meta: [{ title: "Карта скважин — MUNAI" }] }),
  component: MapPage,
});

const colorByStatus: Record<string, string> = {
  active: "var(--color-success)",
  warning: "var(--color-warning)",
  inactive: "var(--color-muted-foreground)",
  broken: "var(--color-destructive)",
};

function MapPage() {
  const [sel, setSel] = useState<ApiWell | null>(null);

  const { data: wells = [], isLoading } = useQuery({
    queryKey: ["wells-map"],
    queryFn: () => wellsApi.list(),
    refetchInterval: 30000,
  });

  // Normalize lat/lng to 5%-95% of the container
  const normalized = wells.map((w) => {
    const lats = wells.map((x) => x.lat);
    const lngs = wells.map((x) => x.lng);
    const minLat = Math.min(...lats), maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
    const rangeX = maxLng - minLng || 1;
    const rangeY = maxLat - minLat || 1;
    return {
      ...w,
      mapX: 5 + ((w.lng - minLng) / rangeX) * 90,
      mapY: 5 + ((w.lat - minLat) / rangeY) * 90,
    };
  });

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-5">
      <div>
        <h1 className="text-3xl md:text-4xl font-bold">Карта скважин</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Интерактивная карта · {wells.length} скважин · нажмите для деталей
        </p>
      </div>

      <div className="flex flex-wrap gap-3 text-xs">
        {[
          { c: "var(--color-success)", l: "Активные" },
          { c: "var(--color-warning)", l: "Внимание" },
          { c: "var(--color-destructive)", l: "Авария" },
          { c: "var(--color-muted-foreground)", l: "Неактивные" },
        ].map((item) => (
          <div key={item.l} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-card border border-border">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: item.c }} /> {item.l}
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 relative rounded-2xl border border-border bg-card overflow-hidden" style={{ aspectRatio: "16/10" }}>
          <div className="absolute inset-0 bg-[linear-gradient(to_right,oklch(0.92_0.005_250/.5)_1px,transparent_1px),linear-gradient(to_bottom,oklch(0.92_0.005_250/.5)_1px,transparent_1px)] [background-size:40px_40px]" />
          <div className="absolute inset-0 munai-grad opacity-30" />
          <div className="absolute top-3 left-3 text-xs bg-card/90 backdrop-blur px-3 py-1.5 rounded-full border border-border">
            Месторождение Узень-3 · Мангистау
          </div>
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          )}
          {normalized.map((w) => (
            <button
              key={w.id}
              onClick={() => setSel(w)}
              className="absolute -translate-x-1/2 -translate-y-1/2 group"
              style={{ left: `${w.mapX}%`, top: `${w.mapY}%` }}
              aria-label={w.code}
            >
              <span className="block h-3.5 w-3.5 rounded-full ring-4 ring-background/70 group-hover:ring-primary/30 transition" style={{ background: colorByStatus[w.status] }} />
              {(w.status === "warning" || w.status === "broken") && (
                <span className="absolute inset-0 rounded-full animate-ping opacity-70" style={{ background: colorByStatus[w.status] }} />
              )}
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[10px] font-semibold whitespace-nowrap opacity-0 group-hover:opacity-100 transition bg-card border border-border px-2 py-0.5 rounded">
                {w.code}
              </span>
            </button>
          ))}
        </div>

        <div className="rounded-2xl border border-border bg-card p-5">
          {sel ? (
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="font-bold text-lg">{sel.code}</div>
                  <div className="text-xs text-muted-foreground">{sel.name}</div>
                </div>
                <StatusBadge status={sel.status} />
              </div>
              <div className="grid grid-cols-2 gap-2">
                {[
                  ["Добыча/24ч", `${sel.production24h} м³`],
                  ["Температура", `${sel.temperature} °C`],
                  ["P внутри НКТ", `${sel.tubing_internal_p} атм`],
                  ["P снаружи НКТ", `${sel.tubing_external_p} атм`],
                  ["Затрубное", `${sel.annulus_p} атм`],
                  ["Качаний/мин", `${sel.pump_strokes}`],
                ].map(([l, v]) => (
                  <div key={l} className="rounded-lg bg-muted/50 p-3">
                    <div className="text-[10px] uppercase text-muted-foreground tracking-wider">{l}</div>
                    <div className="text-sm font-semibold mt-0.5">{v}</div>
                  </div>
                ))}
              </div>
              {sel.operator_name && (
                <div className="text-xs text-muted-foreground">Оператор: {sel.operator_name}</div>
              )}
              {sel.last_report && (
                <div className="text-xs text-muted-foreground">Последний замер: {sel.last_report}</div>
              )}
              <Link to="/app/reports/new">
                <Button className="w-full h-11"><Plus className="h-4 w-4 mr-2" /> Создать отчёт</Button>
              </Link>
            </div>
          ) : (
            <div className="text-center text-sm text-muted-foreground py-12">
              Нажмите на любую скважину на карте,<br /> чтобы увидеть детали
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
