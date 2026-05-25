import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Mic, Upload, FileText, Image as ImageIcon, Sparkles, ChevronLeft, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { wellsApi, reportsApi } from "@/lib/api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export const Route = createFileRoute("/app/reports/new")({
  head: () => ({ meta: [{ title: "Новый отчёт — MUNAI" }] }),
  component: NewReportPage,
});

function NewReportPage() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const [tab, setTab] = useState<"voice" | "manual">("manual");
  const [listening, setListening] = useState(false);

  // Form fields
  const [wellId, setWellId] = useState("");
  const [temperature, setTemperature] = useState("");
  const [production, setProduction] = useState("");
  const [tubingIn, setTubingIn] = useState("");
  const [tubingOut, setTubingOut] = useState("");
  const [annulus, setAnnulus] = useState("");
  const [pumpStrokes, setPumpStrokes] = useState("");
  const [comment, setComment] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { data: wells = [] } = useQuery({
    queryKey: ["wells"],
    queryFn: () => wellsApi.list(),
  });

  const createReport = useMutation({
    mutationFn: reportsApi.create,
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      qc.invalidateQueries({ queryKey: ["dashboard-stats"] });
      qc.invalidateQueries({ queryKey: ["notifications"] });
      if (r.flag) {
        toast.warning(`AI обнаружил: ${r.flag} (score: ${r.ai_score}/100)`);
      } else {
        toast.success(`Отчёт отправлен. AI score: ${r.ai_score}/100`);
      }
      nav({ to: "/app/reports" });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const validate = () => {
    const e: Record<string, string> = {};
    if (!wellId) e.wellId = "Выберите скважину";
    return e;
  };

  const handleSubmit = (ev: React.FormEvent) => {
    ev.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    createReport.mutate({
      well_id: wellId,
      temperature: parseFloat(temperature) || undefined,
      production24h: parseFloat(production) || undefined,
      tubing_internal_p: parseFloat(tubingIn) || undefined,
      tubing_external_p: parseFloat(tubingOut) || undefined,
      annulus_p: parseFloat(annulus) || undefined,
      pump_strokes: parseInt(pumpStrokes) || undefined,
      comment: comment.trim() || undefined,
    });
  };

  const handleVoice = () => {
    setListening((v) => !v);
    if (!listening) {
      toast.info("Запись началась…");
    } else {
      // Simulate voice recognition filling the form
      toast.success("AI распознал параметры. Проверьте форму и отправьте.");
      setTab("manual");
      if (wells.length > 0) setWellId(wells[0].id);
      setTemperature("78");
      setProduction("42");
      setTubingIn("120");
      setTubingOut("45");
      setAnnulus("8");
      setPumpStrokes("6");
      setListening(false);
    }
  };

  return (
    <div className="p-4 md:p-8 max-w-3xl mx-auto space-y-5">
      <button onClick={() => nav({ to: "/app/reports" })} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ChevronLeft className="h-4 w-4" /> К отчётам
      </button>
      <div>
        <h1 className="text-3xl md:text-4xl font-bold">Новый отчёт</h1>
        <p className="text-sm text-muted-foreground mt-1">Выберите удобный способ — голос или вручную</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <button onClick={() => setTab("voice")} className={`rounded-2xl border-2 p-5 text-left transition ${tab === "voice" ? "border-primary bg-accent" : "border-border bg-card hover:border-primary/40"}`}>
          <Mic className="h-6 w-6 text-primary" />
          <div className="font-semibold mt-3">Голосовой ввод</div>
          <div className="text-xs text-muted-foreground">Просто продиктуйте параметры</div>
        </button>
        <button onClick={() => setTab("manual")} className={`rounded-2xl border-2 p-5 text-left transition ${tab === "manual" ? "border-primary bg-accent" : "border-border bg-card hover:border-primary/40"}`}>
          <FileText className="h-6 w-6 text-primary" />
          <div className="font-semibold mt-3">Заполнить форму</div>
          <div className="text-xs text-muted-foreground">Ввести параметры вручную</div>
        </button>
      </div>

      {tab === "voice" && (
        <div className="rounded-2xl border border-border bg-card p-8 text-center">
          <button
            onClick={handleVoice}
            className={`mx-auto h-32 w-32 rounded-full grid place-items-center transition ${listening ? "bg-primary text-primary-foreground animate-pulse" : "bg-accent text-primary"}`}
          >
            <Mic className="h-12 w-12" />
          </button>
          <div className="mt-4 font-semibold">{listening ? "Слушаю…" : "Нажмите и говорите"}</div>
          <p className="text-sm text-muted-foreground mt-1">Пример: «Скважина UZ-104, температура 78 градусов, давление 120 атмосфер»</p>
        </div>
      )}

      {tab === "manual" && (
        <form onSubmit={handleSubmit} className="rounded-2xl border border-border bg-card p-6 space-y-4">
          <div className="space-y-2">
            <Label>Скважина</Label>
            <Select value={wellId} onValueChange={setWellId}>
              <SelectTrigger className="h-11">
                <SelectValue placeholder="Выберите скважину…" />
              </SelectTrigger>
              <SelectContent>
                {wells.map((w) => (
                  <SelectItem key={w.id} value={w.id}>{w.code} — {w.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.wellId && <p className="text-xs text-destructive">{errors.wellId}</p>}
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2"><Label>Температура (°C)</Label><Input type="number" value={temperature} onChange={(e) => setTemperature(e.target.value)} className="h-11" placeholder="78" /></div>
            <div className="space-y-2"><Label>Добыча за 24ч (м³)</Label><Input type="number" value={production} onChange={(e) => setProduction(e.target.value)} className="h-11" placeholder="42" /></div>
            <div className="space-y-2"><Label>P внутри НКТ (атм)</Label><Input type="number" value={tubingIn} onChange={(e) => setTubingIn(e.target.value)} className="h-11" placeholder="120" /></div>
            <div className="space-y-2"><Label>P снаружи НКТ (атм)</Label><Input type="number" value={tubingOut} onChange={(e) => setTubingOut(e.target.value)} className="h-11" placeholder="45" /></div>
            <div className="space-y-2"><Label>Затрубное давл. (атм)</Label><Input type="number" value={annulus} onChange={(e) => setAnnulus(e.target.value)} className="h-11" placeholder="8" /></div>
            <div className="space-y-2"><Label>Качаний / мин</Label><Input type="number" value={pumpStrokes} onChange={(e) => setPumpStrokes(e.target.value)} className="h-11" placeholder="6" /></div>
          </div>

          <div className="space-y-2">
            <Label>Комментарий</Label>
            <Textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={3} placeholder="Дополнительная информация…" />
          </div>

          <div>
            <Label className="mb-2 block">Вложения</Label>
            <div className="grid grid-cols-3 gap-2">
              {[{ i: Upload, l: "PDF/Excel" }, { i: ImageIcon, l: "Фото" }, { i: FileText, l: "Файл" }].map((x) => (
                <button type="button" key={x.l} onClick={() => toast.info("Загрузка файлов будет доступна в следующей версии")} className="rounded-xl border-2 border-dashed border-border p-4 flex flex-col items-center gap-1 text-xs text-muted-foreground hover:border-primary hover:text-primary transition">
                  <x.i className="h-5 w-5" /> {x.l}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground rounded-lg bg-accent p-3">
            <Sparkles className="h-4 w-4 text-primary shrink-0" />
            AI проверит отчёт на аномалии и автоматически уведомит менеджера
          </div>

          <div className="flex gap-2">
            <Button type="button" variant="outline" className="h-11" onClick={() => nav({ to: "/app/reports" })}>Отмена</Button>
            <Button type="submit" className="h-11 flex-1" disabled={createReport.isPending}>
              {createReport.isPending ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Отправка…</> : "Отправить отчёт"}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
