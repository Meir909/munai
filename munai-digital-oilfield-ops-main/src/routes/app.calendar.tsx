import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useSession } from "@/lib/session";
import { Plus, CalendarDays, Loader2, Trash2 } from "lucide-react";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { calendarApi } from "@/lib/api";
import { toast } from "sonner";
import { format, parseISO } from "date-fns";
import { ru } from "date-fns/locale";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export const Route = createFileRoute("/app/calendar")({
  head: () => ({ meta: [{ title: "Календарь — MUNAI" }] }),
  component: CalendarPage,
});

function CalendarPage() {
  const { role } = useSession();
  const qc = useQueryClient();
  const canEdit = role !== "operator";
  const [showAdd, setShowAdd] = useState(false);

  const { data: events = [], isLoading } = useQuery({
    queryKey: ["calendar"],
    queryFn: calendarApi.list,
    refetchInterval: 60000,
  });

  const deleteEvent = useMutation({
    mutationFn: (id: string) => calendarApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["calendar"] }); toast.success("Событие удалено"); },
    onError: (e: Error) => toast.error(e.message),
  });

  // Build calendar days for current month
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const firstDay = new Date(year, month, 1).getDay(); // 0=Sun
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const startOffset = (firstDay + 6) % 7; // Make Monday first day

  const eventDates = events.map((e) => new Date(e.date).getDate());

  return (
    <div className="p-4 md:p-8 max-w-6xl mx-auto space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold">Календарь событий</h1>
          <p className="text-sm text-muted-foreground mt-1 capitalize">
            {format(now, "LLLL yyyy", { locale: ru })}
          </p>
        </div>
        {canEdit && (
          <Button size="lg" className="h-11" onClick={() => setShowAdd(true)}>
            <Plus className="h-4 w-4 mr-2" /> Создать событие
          </Button>
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 rounded-2xl border border-border bg-card p-5">
          <div className="grid grid-cols-7 gap-1 text-center text-xs font-semibold text-muted-foreground mb-2">
            {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((d) => <div key={d}>{d}</div>)}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {Array.from({ length: startOffset }).map((_, i) => (
              <div key={`blank-${i}`} className="aspect-square" />
            ))}
            {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => {
              const hasEvent = eventDates.includes(day);
              const isToday = day === now.getDate();
              return (
                <div key={day} className={`aspect-square rounded-lg border p-2 text-sm relative flex items-start justify-start ${isToday ? "bg-primary text-primary-foreground border-primary" : hasEvent ? "bg-primary/10 border-primary/30" : "border-border"}`}>
                  {day}
                  {hasEvent && !isToday && <span className="absolute bottom-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-primary" />}
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card">
          <div className="p-4 border-b border-border flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-primary" />
            <h3 className="font-semibold">Предстоящие</h3>
          </div>
          {isLoading && <div className="p-8 flex justify-center"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>}
          <div className="divide-y divide-border">
            {events.map((e) => (
              <div key={e.id} className="p-4 flex items-start gap-3">
                <div className="flex-1">
                  <div className="text-xs uppercase tracking-wider text-primary font-semibold">{e.event_type}</div>
                  <div className="font-semibold text-sm mt-0.5">{e.title}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {format(parseISO(e.date), "d MMMM, HH:mm", { locale: ru })}
                  </div>
                </div>
                {canEdit && (
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive" onClick={() => deleteEvent.mutate(e.id)}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                )}
              </div>
            ))}
            {!isLoading && events.length === 0 && (
              <div className="p-8 text-center text-sm text-muted-foreground">Событий нет</div>
            )}
          </div>
        </div>
      </div>

      <EventFormModal
        open={showAdd}
        onClose={() => setShowAdd(false)}
        onSaved={() => { qc.invalidateQueries({ queryKey: ["calendar"] }); setShowAdd(false); }}
      />
    </div>
  );
}

function EventFormModal({ open, onClose, onSaved }: { open: boolean; onClose: () => void; onSaved: () => void }) {
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [eventType, setEventType] = useState("Событие");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !date) return;
    setLoading(true);
    try {
      await calendarApi.create({ title: title.trim(), date: new Date(date).toISOString(), event_type: eventType });
      toast.success("Событие создано");
      onSaved();
      setTitle(""); setDate(""); setEventType("Событие");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-sm">
        <DialogHeader><DialogTitle>Новое событие</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="space-y-2">
            <Label>Название</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} className="h-11" placeholder="Плановый осмотр UZ-104" />
          </div>
          <div className="space-y-2">
            <Label>Дата и время</Label>
            <Input type="datetime-local" value={date} onChange={(e) => setDate(e.target.value)} className="h-11" />
          </div>
          <div className="space-y-2">
            <Label>Тип</Label>
            <select value={eventType} onChange={(e) => setEventType(e.target.value)} className="h-11 w-full rounded-lg border border-border bg-background px-3 text-sm">
              <option>Событие</option>
              <option>Осмотр</option>
              <option>Совещание</option>
              <option>Обучение</option>
              <option>Дедлайн</option>
            </select>
          </div>
          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" className="h-11 flex-1" onClick={onClose}>Отмена</Button>
            <Button type="submit" className="h-11 flex-1" disabled={loading}>
              {loading ? "Создание…" : "Создать"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
