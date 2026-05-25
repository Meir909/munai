import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Search, Plus, ShieldAlert, Trash2, Pencil, Loader2 } from "lucide-react";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { usersApi, type ApiUser } from "@/lib/api";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export const Route = createFileRoute("/app/admin")({
  head: () => ({ meta: [{ title: "Админ-панель — MUNAI" }] }),
  component: AdminPage,
});

function AdminPage() {
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [editUser, setEditUser] = useState<ApiUser | null>(null);

  const { data: users = [], isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: usersApi.list,
  });

  const filtered = users.filter((u) =>
    u.name.toLowerCase().includes(q.toLowerCase()) || u.email.toLowerCase().includes(q.toLowerCase())
  );

  const deleteUser = useMutation({
    mutationFn: (id: string) => usersApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); toast.success("Пользователь удалён"); },
    onError: (e: Error) => toast.error(e.message),
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => usersApi.update(id, { active }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); toast.success("Статус обновлён"); },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="p-4 md:p-8 max-w-6xl mx-auto space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold flex items-center gap-2"><ShieldAlert className="h-8 w-8 text-primary" /> Админ-панель</h1>
          <p className="text-sm text-muted-foreground mt-1">Управление пользователями и правами · {users.length} пользователей</p>
        </div>
        <Button size="lg" className="h-11" onClick={() => setShowAdd(true)}>
          <Plus className="h-4 w-4 mr-2" /> Добавить пользователя
        </Button>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Поиск пользователя…" className="pl-9 h-11" />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
      ) : (
        <div className="rounded-2xl border border-border bg-card overflow-hidden">
          <div className="grid grid-cols-12 px-5 py-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground bg-muted/50 border-b border-border">
            <div className="col-span-4">Сотрудник</div>
            <div className="col-span-3">Email</div>
            <div className="col-span-2">Роль</div>
            <div className="col-span-2">Статус</div>
            <div className="col-span-1 text-right">Действия</div>
          </div>
          {filtered.map((u) => (
            <div key={u.id} className="grid grid-cols-12 items-center px-5 py-3 border-b border-border last:border-0 hover:bg-muted/20 transition">
              <div className="col-span-4 flex items-center gap-3">
                <div className="h-9 w-9 rounded-full bg-primary text-primary-foreground grid place-items-center text-sm font-bold">{u.name.charAt(0)}</div>
                <div>
                  <div className="font-medium text-sm">{u.name}</div>
                  {u.position && <div className="text-xs text-muted-foreground">{u.position}</div>}
                </div>
              </div>
              <div className="col-span-3 text-sm text-muted-foreground truncate">{u.email}</div>
              <div className="col-span-2">
                <span className="text-xs px-2 py-1 rounded-full bg-accent text-accent-foreground capitalize">{u.role}</span>
              </div>
              <div className="col-span-2">
                <button onClick={() => toggleActive.mutate({ id: u.id, active: !u.active })} className={`text-xs px-2 py-1 rounded-full transition ${u.active ? "bg-success/10 text-success hover:bg-success/20" : "bg-muted text-muted-foreground hover:bg-muted/80"}`}>
                  {u.active ? "Активен" : "Отключён"}
                </button>
              </div>
              <div className="col-span-1 flex items-center justify-end gap-1">
                <Button variant="ghost" size="sm" onClick={() => setEditUser(u)} className="h-8 w-8 p-0">
                  <Pencil className="h-3.5 w-3.5" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => deleteUser.mutate(u.id)} disabled={deleteUser.isPending} className="h-8 w-8 p-0 text-destructive hover:text-destructive">
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="py-12 text-center text-muted-foreground">Пользователи не найдены</div>
          )}
        </div>
      )}

      <UserFormModal
        open={showAdd || !!editUser}
        onClose={() => { setShowAdd(false); setEditUser(null); }}
        existing={editUser}
        onSaved={() => { qc.invalidateQueries({ queryKey: ["users"] }); setShowAdd(false); setEditUser(null); }}
      />
    </div>
  );
}

function UserFormModal({ open, onClose, existing, onSaved }: { open: boolean; onClose: () => void; existing: ApiUser | null; onSaved: () => void }) {
  const [name, setName] = useState(existing?.name ?? "");
  const [email, setEmail] = useState(existing?.email ?? "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"operator" | "manager" | "director" | "admin">(existing?.role ?? "operator");
  const [position, setPosition] = useState(existing?.position ?? "");
  const [region, setRegion] = useState(existing?.region ?? "");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const e: Record<string, string> = {};
    if (!name.trim()) e.name = "Введите имя";
    if (!existing && !email.trim()) e.email = "Введите email";
    if (!existing && password.length < 4) e.password = "Минимум 4 символа";
    return e;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;
    setLoading(true);
    try {
      if (existing) {
        const update: Record<string, unknown> = { name, role, position, region };
        if (password) update.password = password;
        await usersApi.update(existing.id, update);
        toast.success("Пользователь обновлён");
      } else {
        await usersApi.create({ name, email, password, role, position, region });
        toast.success("Пользователь создан");
      }
      onSaved();
      onClose();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{existing ? "Редактировать пользователя" : "Новый пользователь"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="space-y-2">
            <Label>Имя</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} className="h-11" />
            {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
          </div>
          {!existing && (
            <div className="space-y-2">
              <Label>Email</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="h-11" />
              {errors.email && <p className="text-xs text-destructive">{errors.email}</p>}
            </div>
          )}
          <div className="space-y-2">
            <Label>{existing ? "Новый пароль (необязательно)" : "Пароль"}</Label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="h-11" />
            {errors.password && <p className="text-xs text-destructive">{errors.password}</p>}
          </div>
          <div className="space-y-2">
            <Label>Роль</Label>
            <select value={role} onChange={(e) => setRole(e.target.value as "operator" | "manager" | "director" | "admin")} className="h-11 w-full rounded-lg border border-border bg-background px-3 text-sm">
              <option value="operator">Оператор</option>
              <option value="manager">Менеджер</option>
              <option value="director">Директор</option>
              <option value="admin">Администратор</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Должность</Label>
              <Input value={position} onChange={(e) => setPosition(e.target.value)} className="h-11" />
            </div>
            <div className="space-y-2">
              <Label>Регион</Label>
              <Input value={region} onChange={(e) => setRegion(e.target.value)} className="h-11" />
            </div>
          </div>
          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" className="h-11 flex-1" onClick={onClose}>Отмена</Button>
            <Button type="submit" className="h-11 flex-1" disabled={loading}>
              {loading ? "Сохранение…" : existing ? "Сохранить" : "Создать"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
