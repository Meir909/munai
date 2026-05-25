import { createFileRoute, Link } from "@tanstack/react-router";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Plus, Sparkles, Filter, Loader2, Trash2 } from "lucide-react";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reportsApi } from "@/lib/api";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";
import { ru } from "date-fns/locale";
import { useSession } from "@/lib/session";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export const Route = createFileRoute("/app/reports")({
  head: () => ({ meta: [{ title: "Отчёты — MUNAI" }] }),
  component: ReportsPage,
});

function ReportsPage() {
  const { role } = useSession();
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["reports", q, statusFilter],
    queryFn: () => reportsApi.list(q, statusFilter),
    refetchInterval: 30000,
  });

  const deleteReport = useMutation({
    mutationFn: (id: string) => reportsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["reports"] }); toast.success("Отчёт удалён"); },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold">Отчёты</h1>
          <p className="text-sm text-muted-foreground mt-1">{reports.length} отчётов · AI-валидация активна</p>
        </div>
        <Link to="/app/reports/new"><Button size="lg" className="h-11"><Plus className="h-4 w-4 mr-2" /> Новый отчёт</Button></Link>
      </div>

      <div className="flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Поиск по скважине или оператору…" className="pl-9 h-11" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="h-11 w-40">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Все статусы</SelectItem>
            <SelectItem value="pending">Ожидает</SelectItem>
            <SelectItem value="approved">Одобрен</SelectItem>
            <SelectItem value="flagged">Аномалия</SelectItem>
            <SelectItem value="rejected">Отклонён</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="rounded-2xl border border-border bg-card overflow-hidden">
          <div className="divide-y divide-border">
            {reports.map((r) => (
              <div key={r.id} className="p-4 md:p-5 flex flex-wrap items-center gap-4 hover:bg-muted/30 transition">
                <div className="h-12 w-12 rounded-xl bg-accent grid place-items-center font-bold text-accent-foreground">
                  {r.well_code?.split("-")[1]}
                </div>
                <div className="flex-1 min-w-[200px]">
                  <div className="font-semibold">{r.well_code}</div>
                  <div className="text-sm text-muted-foreground">{r.summary}</div>
                  {r.flag && <div className="text-xs text-warning-foreground mt-1">⚠ {r.flag}</div>}
                </div>
                <div className="text-xs text-muted-foreground">
                  <div>{r.operator_name}</div>
                  <div>{formatDistanceToNow(new Date(r.created_at), { addSuffix: true, locale: ru })}</div>
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Sparkles className="h-3.5 w-3.5 text-primary" /> AI {r.ai_score}/100
                </div>
                <StatusBadge status={r.status} />
                {(role === "admin" || role === "director") && (
                  <Button variant="ghost" size="sm" className="h-9 text-destructive hover:text-destructive" onClick={() => deleteReport.mutate(r.id)} disabled={deleteReport.isPending}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
            {reports.length === 0 && (
              <div className="py-20 text-center text-muted-foreground">Отчёты не найдены</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
