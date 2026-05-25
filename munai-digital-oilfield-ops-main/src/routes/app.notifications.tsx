import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notificationsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCheck } from "lucide-react";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";
import { ru } from "date-fns/locale";

export const Route = createFileRoute("/app/notifications")({
  head: () => ({ meta: [{ title: "Уведомления — MUNAI" }] }),
  component: NotificationsPage,
});

function NotificationsPage() {
  const qc = useQueryClient();

  const { data: notifications = [], isLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: notificationsApi.list,
    refetchInterval: 30000,
  });

  const markRead = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllRead = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["notifications"] }); toast.success("Все уведомления прочитаны"); },
  });

  const unreadCount = notifications.filter((n) => n.unread).length;

  return (
    <div className="p-4 md:p-8 max-w-3xl mx-auto space-y-5">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold">Уведомления</h1>
          <p className="text-sm text-muted-foreground mt-1">{unreadCount} непрочитанных</p>
        </div>
        {unreadCount > 0 && (
          <Button variant="outline" className="h-10 gap-2" onClick={() => markAllRead.mutate()} disabled={markAllRead.isPending}>
            <CheckCheck className="h-4 w-4" /> Прочитать все
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="rounded-2xl border border-border bg-card divide-y divide-border overflow-hidden">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={`p-5 flex items-start gap-3 ${n.unread ? "bg-accent/40" : ""} cursor-pointer hover:bg-muted/30 transition`}
              onClick={() => n.unread && markRead.mutate(n.id)}
            >
              <span className={`mt-2 h-2.5 w-2.5 rounded-full shrink-0 ${n.tone === "warning" ? "bg-warning" : n.tone === "success" ? "bg-success" : n.tone === "destructive" ? "bg-destructive" : "bg-info"}`} />
              <div className="flex-1">
                <div className="font-semibold">{n.title}</div>
                <div className="text-sm text-muted-foreground mt-0.5">{n.body}</div>
                <div className="text-xs text-muted-foreground mt-1.5">
                  {formatDistanceToNow(new Date(n.created_at), { addSuffix: true, locale: ru })}
                </div>
              </div>
              {n.unread && <span className="text-[10px] uppercase tracking-wider bg-primary text-primary-foreground px-2 py-0.5 rounded-full shrink-0">Новое</span>}
            </div>
          ))}
          {notifications.length === 0 && (
            <div className="py-20 text-center text-muted-foreground">Нет уведомлений</div>
          )}
        </div>
      )}
    </div>
  );
}
