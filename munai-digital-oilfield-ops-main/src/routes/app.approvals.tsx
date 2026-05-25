import { createFileRoute } from "@tanstack/react-router";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Sparkles, Check, X, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reportsApi } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { ru } from "date-fns/locale";

export const Route = createFileRoute("/app/approvals")({
  head: () => ({ meta: [{ title: "Согласования — MUNAI" }] }),
  component: ApprovalsPage,
});

function ApprovalsPage() {
  const qc = useQueryClient();

  const { data: pending = [], isLoading } = useQuery({
    queryKey: ["reports-pending"],
    queryFn: reportsApi.pending,
    refetchInterval: 30000,
  });

  const reviewReport = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "approved" | "rejected" }) =>
      reportsApi.review(id, status),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["reports-pending"] });
      qc.invalidateQueries({ queryKey: ["reports"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
      qc.invalidateQueries({ queryKey: ["notifications"] });
      toast[vars.status === "approved" ? "success" : "error"](
        vars.status === "approved" ? "Отчёт одобрен" : "Отчёт отклонён"
      );
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto space-y-5">
      <div>
        <h1 className="text-3xl md:text-4xl font-bold">Центр согласований</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {isLoading ? "Загрузка…" : `${pending.length} отчётов ожидают вашего решения`}
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      <div className="space-y-3">
        {pending.map((r) => (
          <div key={r.id} className="rounded-2xl border border-border bg-card p-5">
            <div className="flex flex-wrap items-start gap-4">
              <div className="h-12 w-12 rounded-xl bg-accent grid place-items-center font-bold">{r.well_code?.split("-")[1]}</div>
              <div className="flex-1 min-w-[200px]">
                <div className="flex items-center gap-2">
                  <div className="font-semibold">{r.well_code}</div>
                  <StatusBadge status={r.status} />
                </div>
                <div className="text-sm text-muted-foreground mt-1">{r.summary}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {r.operator_name} · {formatDistanceToNow(new Date(r.created_at), { addSuffix: true, locale: ru })}
                </div>
                {/* Parameters */}
                {(r.temperature || r.production24h) && (
                  <div className="flex flex-wrap gap-3 mt-3 text-xs text-muted-foreground">
                    {r.temperature && <span>Темп: {r.temperature}°C</span>}
                    {r.production24h && <span>Добыча: {r.production24h} м³</span>}
                    {r.tubing_internal_p && <span>P НКТ: {r.tubing_internal_p} атм</span>}
                    {r.annulus_p && <span>Затруб: {r.annulus_p} атм</span>}
                  </div>
                )}
                {r.flag && (
                  <div className="mt-3 rounded-lg bg-warning/10 border border-warning/20 p-3 text-xs flex items-start gap-2">
                    <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                    <div>
                      <div className="font-medium">AI обнаружил: {r.flag}</div>
                      <div className="text-muted-foreground mt-0.5">Рекомендуется отправить оператору на доработку или подтвердить вручную.</div>
                    </div>
                  </div>
                )}
                {r.comment && (
                  <div className="mt-2 text-xs text-muted-foreground italic">Комментарий: {r.comment}</div>
                )}
              </div>
              <div className="flex flex-col gap-2 w-full md:w-auto">
                <div className="flex items-center gap-1 text-xs text-muted-foreground justify-end">
                  <Sparkles className="h-3.5 w-3.5 text-primary" /> AI score: {r.ai_score}/100
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="h-10"
                    onClick={() => reviewReport.mutate({ id: r.id, status: "rejected" })}
                    disabled={reviewReport.isPending}
                  >
                    <X className="h-4 w-4 mr-1" /> Отклонить
                  </Button>
                  <Button
                    className="h-10"
                    onClick={() => reviewReport.mutate({ id: r.id, status: "approved" })}
                    disabled={reviewReport.isPending}
                  >
                    {reviewReport.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4 mr-1" />}
                    Одобрить
                  </Button>
                </div>
              </div>
            </div>
          </div>
        ))}
        {!isLoading && pending.length === 0 && (
          <div className="py-20 text-center rounded-2xl border border-border bg-card text-muted-foreground">
            Нет отчётов для согласования
          </div>
        )}
      </div>
    </div>
  );
}
