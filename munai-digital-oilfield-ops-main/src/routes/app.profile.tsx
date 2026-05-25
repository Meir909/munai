import { createFileRoute } from "@tanstack/react-router";
import { useSession } from "@/lib/session";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { usersApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { toast } from "sonner";

export const Route = createFileRoute("/app/profile")({
  head: () => ({ meta: [{ title: "Профиль — MUNAI" }] }),
  component: ProfilePage,
});

function ProfilePage() {
  const { user } = useSession();
  const { updateUser } = useAuthStore();

  const [name, setName] = useState(user.name);
  const [position, setPosition] = useState(user.position);
  const [region, setRegion] = useState(user.region);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPasswordForm, setShowPasswordForm] = useState(false);

  const updateProfile = useMutation({
    mutationFn: (body: { name?: string; position?: string; region?: string }) =>
      usersApi.update(user.id, body),
    onSuccess: (updated) => {
      updateUser(updated);
      toast.success("Профиль обновлён");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const changePassword = useMutation({
    mutationFn: (password: string) => usersApi.update(user.id, { password }),
    onSuccess: () => {
      toast.success("Пароль изменён");
      setNewPassword("");
      setConfirmPassword("");
      setShowPasswordForm(false);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { toast.error("Введите имя"); return; }
    updateProfile.mutate({ name: name.trim(), position: position.trim(), region: region.trim() });
  };

  const handlePasswordChange = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 4) { toast.error("Минимум 4 символа"); return; }
    if (newPassword !== confirmPassword) { toast.error("Пароли не совпадают"); return; }
    changePassword.mutate(newPassword);
  };

  return (
    <div className="p-4 md:p-8 max-w-3xl mx-auto space-y-5">
      <h1 className="text-3xl md:text-4xl font-bold">Профиль</h1>

      <form onSubmit={handleSave} className="rounded-2xl border border-border bg-card p-6">
        <div className="flex items-center gap-4">
          <div className="h-20 w-20 rounded-2xl bg-primary text-primary-foreground grid place-items-center text-2xl font-bold">
            {user.name.charAt(0)}
          </div>
          <div>
            <div className="text-2xl font-bold">{user.name}</div>
            <div className="text-sm text-muted-foreground">{user.position}</div>
            <div className="text-xs text-muted-foreground mt-1">{user.region}</div>
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-4 mt-6">
          <div className="space-y-2">
            <Label>Имя</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} className="h-11" />
          </div>
          <div className="space-y-2">
            <Label>Email</Label>
            <Input value={user.email} disabled className="h-11 opacity-60" />
          </div>
          <div className="space-y-2">
            <Label>Должность</Label>
            <Input value={position} onChange={(e) => setPosition(e.target.value)} className="h-11" />
          </div>
          <div className="space-y-2">
            <Label>Регион</Label>
            <Input value={region} onChange={(e) => setRegion(e.target.value)} className="h-11" />
          </div>
        </div>
        <div className="mt-6 flex gap-2">
          <Button type="submit" className="h-11" disabled={updateProfile.isPending}>
            {updateProfile.isPending ? "Сохранение…" : "Сохранить"}
          </Button>
          <Button type="button" variant="outline" className="h-11" onClick={() => setShowPasswordForm((v) => !v)}>
            Сменить пароль
          </Button>
        </div>
      </form>

      {showPasswordForm && (
        <form onSubmit={handlePasswordChange} className="rounded-2xl border border-border bg-card p-6 space-y-4">
          <h3 className="font-semibold">Смена пароля</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Новый пароль</Label>
              <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="h-11" />
            </div>
            <div className="space-y-2">
              <Label>Подтвердить пароль</Label>
              <Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="h-11" />
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="outline" className="h-11" onClick={() => setShowPasswordForm(false)}>Отмена</Button>
            <Button type="submit" className="h-11" disabled={changePassword.isPending}>
              {changePassword.isPending ? "Сохранение…" : "Сохранить пароль"}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
