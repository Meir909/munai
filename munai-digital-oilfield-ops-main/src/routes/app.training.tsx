import { createFileRoute } from "@tanstack/react-router";
// Training modules — static content (no backend needed)
const trainings = [
  { id: "t-1", title: "Основы работы оператора", duration: "12 мин", progress: 100 },
  { id: "t-2", title: "Как подавать отчёт через MUNAI", duration: "8 мин", progress: 65 },
  { id: "t-3", title: "Голосовой ввод и AI-ассистент", duration: "6 мин", progress: 30 },
  { id: "t-4", title: "Техника безопасности на скважине", duration: "20 мин", progress: 0 },
];
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { PlayCircle, GraduationCap } from "lucide-react";

export const Route = createFileRoute("/app/training")({
  head: () => ({ meta: [{ title: "Обучение — MUNAI" }] }),
  component: () => (
    <div className="p-4 md:p-8 max-w-5xl mx-auto space-y-5">
      <div>
        <h1 className="text-3xl md:text-4xl font-bold flex items-center gap-2">
          <GraduationCap className="h-8 w-8 text-primary" /> Центр обучения
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Короткие видео и инструкции для сотрудников</p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {trainings.map((t) => (
          <div key={t.id} className="rounded-2xl border border-border bg-card p-5">
            <div className="flex items-start gap-3">
              <div className="h-14 w-14 rounded-xl bg-accent grid place-items-center text-primary"><PlayCircle className="h-7 w-7" /></div>
              <div className="flex-1">
                <div className="font-semibold">{t.title}</div>
                <div className="text-xs text-muted-foreground">{t.duration} · {t.progress === 100 ? "Завершено" : t.progress > 0 ? "В процессе" : "Не начато"}</div>
              </div>
            </div>
            <Progress value={t.progress} className="mt-4" />
            <div className="mt-4 flex justify-between items-center">
              <div className="text-xs text-muted-foreground">{t.progress}% завершено</div>
              <Button size="sm" className="h-9">{t.progress === 100 ? "Повторить" : t.progress > 0 ? "Продолжить" : "Начать"}</Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  ),
});
