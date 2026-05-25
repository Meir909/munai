import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Plus, Droplets, Loader2, Pencil, Trash2, X } from "lucide-react";
import { StatusBadge } from "@/components/status-badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { wellsApi, type ApiWell } from "@/lib/api";
import { toast } from "sonner";
import { useSession } from "@/lib/session";

export const Route = createFileRoute("/app/wells")({
  head: () => ({ meta: [{ title: "Скважины — MUNAI" }] }),
  component: WellsPage,
});

function WellsPage() {
  const { role } = useSession();
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [editWell, setEditWell] = useState<ApiWell | null>(null);

  const { data: wells = [], isLoading } = useQuery({
    queryKey: ["wells", q, filter],
    queryFn: () => wellsApi.list(q, filter),
    refetchInterval: 30000,
  });

  const selected = wells.find((w) => w.id === selectedId);

  const deleteWell = useMutation({
    mutationFn: (id: string) => wellsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["wells"] });
      toast.success("Скважина удалена");
      setSelectedId(null);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold">Скважины</h1>
          <p className="text-sm text-muted-foreground mt-1">{wells.length} скважин · {isLoading ? "загрузка…" : "данные актуальны"}</p>
        </div>
        {(role === "manager" || role === "director" || role === "admin") && (
          <Button size="lg" className="h-11" onClick={() => setShowAdd(true)}>
            <Plus className="h-4 w-4 mr-2" /> Добавить скважину
          </Button>
        )}
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Поиск по коду или названию…" className="pl-9 h-11" />
        </div>
        {[
          { v: "all", l: "Все" },
          { v: "active", l: "Активные" },
          { v: "warning", l: "Внимание" },
          { v: "broken", l: "Авария" },
          { v: "inactive", l: "Неактивные" },
        ].map((f) => (
          <Button key={f.v} variant={filter === f.v ? "default" : "outline"} onClick={() => setFilter(f.v)} className="h-11">
            {f.l}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {wells.map((w) => (
            <button key={w.id} onClick={() => setSelectedId(w.id)} className="text-left rounded-2xl border border-border bg-card p-5 hover:border-primary hover:shadow-elevated transition">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-11 w-11 rounded-xl bg-accent grid place-items-center"><Droplets className="h-5 w-5 text-primary" /></div>
                  <div>
                    <div className="font-semibold">{w.code}</div>
                    <div className="text-xs text-muted-foreground">{w.name}</div>
                  </div>
                </div>
                <StatusBadge status={w.status} />
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                <Mini label="Добыча" value={`${w.production24h} м³`} />
                <Mini label="Темп." value={`${w.temperature}°`} />
                <Mini label="Давл." value={`${w.tubing_internal_p} атм`} />
              </div>
            </button>
          ))}
          {wells.length === 0 && (
            <div className="col-span-3 py-20 text-center text-muted-foreground">Скважины не найдены</div>
          )}
        </div>
      )}

      {/* Well detail modal */}
      <Dialog open={!!selectedId} onOpenChange={(v) => !v && setSelectedId(null)}>
        <DialogContent className="max-w-2xl">
          {selected && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-3">
                  <span>{selected.code} · {selected.name}</span>
                  <StatusBadge status={selected.status} />
                </DialogTitle>
                <DialogDescription>
                  Полные параметры скважины · Последний замер: {selected.last_report ?? "нет данных"}
                </DialogDescription>
              </DialogHeader>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-2">
                <Param label="Продукт" value={selected.product === "oil" ? "Нефть" : selected.product === "gas" ? "Газ" : "Конденсат"} />
                <Param label="Добыча/сутки" value={`${selected.production24h} м³`} />
                <Param label="Температура" value={`${selected.temperature} °C`} />
                <Param label="P внутри НКТ" value={`${selected.tubing_internal_p} атм`} />
                <Param label="P снаружи НКТ" value={`${selected.tubing_external_p} атм`} />
                <Param label="Затрубное давл." value={`${selected.annulus_p} атм`} />
                <Param label="Качаний/мин" value={`${selected.pump_strokes}`} />
                <Param label="Оператор" value={selected.operator_name ?? "—"} />
                <Param label="Менеджер" value={selected.manager_name ?? "—"} />
              </div>
              <div className="flex flex-wrap gap-2 mt-4">
                <Link to="/app/reports/new">
                  <Button className="h-10"><Plus className="h-4 w-4 mr-2" /> Создать отчёт</Button>
                </Link>
                {(role === "manager" || role === "director" || role === "admin") && (
                  <Button variant="outline" className="h-10" onClick={() => { setEditWell(selected); setSelectedId(null); }}>
                    <Pencil className="h-4 w-4 mr-2" /> Редактировать
                  </Button>
                )}
                {(role === "director" || role === "admin") && (
                  <Button variant="destructive" className="h-10" onClick={() => deleteWell.mutate(selected.id)} disabled={deleteWell.isPending}>
                    <Trash2 className="h-4 w-4 mr-2" /> Удалить
                  </Button>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Add/Edit well modal */}
      <WellFormModal
        open={showAdd || !!editWell}
        onClose={() => { setShowAdd(false); setEditWell(null); }}
        existing={editWell}
        onSaved={() => { qc.invalidateQueries({ queryKey: ["wells"] }); setShowAdd(false); setEditWell(null); }}
      />
    </div>
  );
}

function WellFormModal({ open, onClose, existing, onSaved }: { open: boolean; onClose: () => void; existing: ApiWell | null; onSaved: () => void }) {
  const [code, setCode] = useState(existing?.code ?? "");
  const [name, setName] = useState(existing?.name ?? "");
  const [status, setStatus] = useState<"active" | "warning" | "inactive" | "broken">(existing?.status ?? "active");
  const [product, setProduct] = useState<"oil" | "gas" | "condensate">(existing?.product ?? "oil");
  const [production, setProduction] = useState(String(existing?.production24h ?? ""));
  const [temp, setTemp] = useState(String(existing?.temperature ?? ""));
  const [loading, setLoading] = useState(false);

  // Reset fields when existing changes
  const resetAndClose = () => {
    setCode(""); setName(""); setStatus("active"); setProduct("oil"); setProduction(""); setTemp("");
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || !name.trim()) return;
    setLoading(true);
    try {
      const body = { code: code.trim(), name: name.trim(), status, product, production24h: parseFloat(production) || 0, temperature: parseFloat(temp) || 0 };
      if (existing) {
        await wellsApi.update(existing.id, body);
        toast.success("Скважина обновлена");
      } else {
        await wellsApi.create(body);
        toast.success("Скважина добавлена");
      }
      onSaved();
      resetAndClose();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && resetAndClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{existing ? "Редактировать скважину" : "Добавить скважину"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Код скважины</Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="UZ-125" className="h-11" disabled={!!existing} />
            </div>
            <div className="space-y-2">
              <Label>Название</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Скважина №125" className="h-11" />
            </div>
            <div className="space-y-2">
              <Label>Статус</Label>
              <select value={status} onChange={(e) => setStatus(e.target.value as "active" | "warning" | "inactive" | "broken")} className="h-11 w-full rounded-lg border border-border bg-background px-3 text-sm">
                <option value="active">Активна</option>
                <option value="warning">Внимание</option>
                <option value="inactive">Неактивна</option>
                <option value="broken">Авария</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Продукт</Label>
              <select value={product} onChange={(e) => setProduct(e.target.value as "oil" | "gas" | "condensate")} className="h-11 w-full rounded-lg border border-border bg-background px-3 text-sm">
                <option value="oil">Нефть</option>
                <option value="gas">Газ</option>
                <option value="condensate">Конденсат</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Добыча/24ч (м³)</Label>
              <Input type="number" value={production} onChange={(e) => setProduction(e.target.value)} className="h-11" />
            </div>
            <div className="space-y-2">
              <Label>Температура (°C)</Label>
              <Input type="number" value={temp} onChange={(e) => setTemp(e.target.value)} className="h-11" />
            </div>
          </div>
          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" className="h-11 flex-1" onClick={resetAndClose}>Отмена</Button>
            <Button type="submit" className="h-11 flex-1" disabled={loading}>
              {loading ? "Сохранение…" : existing ? "Сохранить" : "Добавить"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

const Mini = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-lg bg-muted/50 py-2">
    <div className="text-[10px] uppercase text-muted-foreground tracking-wider">{label}</div>
    <div className="text-sm font-semibold mt-0.5">{value}</div>
  </div>
);
const Param = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-lg border border-border p-3">
    <div className="text-[11px] uppercase text-muted-foreground tracking-wider">{label}</div>
    <div className="text-base font-semibold mt-1">{value}</div>
  </div>
);
