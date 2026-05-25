import { createFileRoute } from "@tanstack/react-router";
import { History, Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { auditApi } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { ru } from "date-fns/locale";

export const Route = createFileRoute("/app/audit")({
  head: () => ({ meta: [{ title: "Журнал действий — MUNAI" }] }),
  component: AuditPage,
});

function AuditPage() {
  const { data: logs = [], isLoading } = useQuery({
    queryKey: ["audit"],
    queryFn: auditApi.list,
    refetchInterval: 60000,
  });

  return (
    <div className="p-4 md:p-8 max-w-4xl mx-auto space-y-5">
      <div>
        <h1 className="text-3xl md:text-4xl font-bold flex items-center gap-2"><History className="h-8 w-8 text-primary" /> Журнал действий</h1>
        <p className="text-sm text-muted-foreground mt-1">Полная история изменений в системе · {logs.length} записей</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
      ) : (
        <div className="rounded-2xl border border-border bg-card overflow-hidden">
          {logs.map((a, i) => (
            <div key={a.id} className="flex items-start gap-4 p-4 border-b border-border last:border-0 hover:bg-muted/20 transition">
              <div className="text-xs text-muted-foreground w-32 shrink-0">
                {formatDistanceToNow(new Date(a.created_at), { addSuffix: true, locale: ru })}
              </div>
              <div className="flex-1">
                <div className="text-sm">
                  <span className="font-semibold">{a.who}</span>{" "}
                  {a.action}{" "}
                  <span className="font-mono bg-muted px-1.5 py-0.5 rounded text-xs">{a.target}</span>
                </div>
              </div>
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground">#{logs.length - i}</span>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="py-12 text-center text-muted-foreground">Журнал пуст</div>
          )}
        </div>
      )}
    </div>
  );
}
