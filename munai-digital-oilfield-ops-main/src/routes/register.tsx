import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState } from "react";
import { toast } from "sonner";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";

export const Route = createFileRoute("/register")({
  head: () => ({ meta: [{ title: "Регистрация — MUNAI" }] }),
  component: RegisterPage,
});

function RegisterPage() {
  const nav = useNavigate();
  const { setAuth } = useAuthStore();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [position, setPosition] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const e: Record<string, string> = {};
    if (!firstName.trim()) e.firstName = "Введите имя";
    if (!lastName.trim()) e.lastName = "Введите фамилию";
    if (!email.trim()) e.email = "Введите email";
    else if (!/\S+@\S+\.\S+/.test(email)) e.email = "Некорректный email";
    if (password.length < 4) e.password = "Минимум 4 символа";
    return e;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setLoading(true);
    try {
      const name = `${firstName.trim()} ${lastName.trim()}`;
      const res = await authApi.register(name, email.trim(), password, "operator", position.trim());
      setAuth(res.access_token, res.user);
      toast.success("Аккаунт создан! Добро пожаловать.");
      nav({ to: "/app/dashboard" });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ошибка регистрации";
      toast.error(msg);
      if (msg.toLowerCase().includes("email")) setErrors((e) => ({ ...e, email: msg }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-10 bg-background">
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-5 rounded-2xl border border-border bg-card p-8 shadow-soft">
        <Link to="/" className="flex items-center gap-2">
          <div className="h-10 w-10 rounded-xl bg-primary grid place-items-center text-primary-foreground font-bold">M</div>
          <span className="font-bold text-xl">MUNAI</span>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">Создать аккаунт</h1>
          <p className="text-sm text-muted-foreground mt-1">Зарегистрируйтесь как сотрудник компании</p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label>Имя</Label>
            <Input className="h-11" value={firstName} onChange={(e) => setFirstName(e.target.value)} disabled={loading} />
            {errors.firstName && <p className="text-xs text-destructive">{errors.firstName}</p>}
          </div>
          <div className="space-y-2">
            <Label>Фамилия</Label>
            <Input className="h-11" value={lastName} onChange={(e) => setLastName(e.target.value)} disabled={loading} />
            {errors.lastName && <p className="text-xs text-destructive">{errors.lastName}</p>}
          </div>
        </div>
        <div className="space-y-2">
          <Label>Email</Label>
          <Input type="email" className="h-11" value={email} onChange={(e) => setEmail(e.target.value)} disabled={loading} />
          {errors.email && <p className="text-xs text-destructive">{errors.email}</p>}
        </div>
        <div className="space-y-2">
          <Label>Пароль</Label>
          <Input type="password" className="h-11" value={password} onChange={(e) => setPassword(e.target.value)} disabled={loading} />
          {errors.password && <p className="text-xs text-destructive">{errors.password}</p>}
        </div>
        <div className="space-y-2">
          <Label>Должность (необязательно)</Label>
          <Input className="h-11" placeholder="Оператор по добыче нефти" value={position} onChange={(e) => setPosition(e.target.value)} disabled={loading} />
        </div>
        <Button type="submit" className="w-full h-11" disabled={loading}>
          {loading ? "Создание аккаунта…" : "Создать аккаунт"}
        </Button>
        <p className="text-sm text-center text-muted-foreground">
          Уже есть аккаунт? <Link to="/login" className="text-primary font-medium hover:underline">Войти</Link>
        </p>
      </form>
    </div>
  );
}
