import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState } from "react";
import { toast } from "sonner";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Вход — MUNAI" }] }),
  component: LoginPage,
});

function LoginPage() {
  const nav = useNavigate();
  const { setAuth } = useAuthStore();
  const [email, setEmail] = useState("operator@munai.kz");
  const [password, setPassword] = useState("demo");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email.trim() || !password.trim()) {
      setError("Введите email и пароль");
      return;
    }
    setLoading(true);
    try {
      const res = await authApi.login(email.trim(), password);
      setAuth(res.access_token, res.user);
      toast.success(`Добро пожаловать, ${res.user.name.split(" ")[0]}!`);
      nav({ to: "/app/dashboard" });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ошибка входа";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex flex-1 bg-sidebar text-sidebar-foreground p-12 flex-col justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="h-10 w-10 rounded-xl bg-primary grid place-items-center text-primary-foreground font-bold">M</div>
          <span className="font-bold text-xl">MUNAI</span>
        </Link>
        <div>
          <h2 className="text-4xl font-bold tracking-tight">AI Digital Oilfield Operations Platform</h2>
          <p className="mt-4 text-sidebar-foreground/70 max-w-md">Единая интеллектуальная система для управления нефтегазовым промыслом — от скважины до совета директоров.</p>
        </div>
        <div className="text-xs text-sidebar-foreground/50">© 2026 MUNAI</div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
        <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-5">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="h-10 w-10 rounded-xl bg-primary grid place-items-center text-primary-foreground font-bold">M</div>
            <span className="font-bold text-xl">MUNAI</span>
          </div>
          <div>
            <h1 className="text-3xl font-bold">Добро пожаловать</h1>
            <p className="text-sm text-muted-foreground mt-1">Войдите в систему MUNAI</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="h-11" disabled={loading} />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Пароль</Label>
              <Link to="/forgot-password" className="text-xs text-primary hover:underline">Забыли?</Link>
            </div>
            <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="h-11" disabled={loading} />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" className="w-full h-11 text-base" disabled={loading}>
            {loading ? "Вход…" : "Войти"}
          </Button>
          <p className="text-sm text-center text-muted-foreground">
            Нет аккаунта? <Link to="/register" className="text-primary font-medium hover:underline">Регистрация</Link>
          </p>
          <div className="text-xs text-center text-muted-foreground p-3 rounded-lg bg-muted/60 space-y-1">
            <div className="font-medium">Демо-аккаунты (пароль: demo)</div>
            <div>operator@munai.kz · manager@munai.kz</div>
            <div>director@munai.kz · admin@munai.kz</div>
          </div>
        </form>
      </div>
    </div>
  );
}
