import { createFileRoute, Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({ meta: [{ title: "Восстановление пароля — MUNAI" }] }),
  component: () => (
    <div className="min-h-screen flex items-center justify-center px-6 py-10 bg-background munai-grad">
      <form
        onSubmit={(e) => { e.preventDefault(); toast.success("Письмо со ссылкой отправлено"); }}
        className="w-full max-w-md space-y-5 rounded-2xl border border-border bg-card p-8 shadow-soft"
      >
        <Link to="/" className="flex items-center gap-2">
          <div className="h-10 w-10 rounded-xl bg-primary grid place-items-center text-primary-foreground font-bold">M</div>
          <span className="font-bold text-xl">MUNAI</span>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">Восстановление пароля</h1>
          <p className="text-sm text-muted-foreground mt-1">Введите email — мы отправим ссылку для сброса.</p>
        </div>
        <div className="space-y-2"><Label>Email</Label><Input type="email" className="h-11" placeholder="you@munai.kz" /></div>
        <Button type="submit" className="w-full h-11">Отправить ссылку</Button>
        <p className="text-sm text-center text-muted-foreground">
          <Link to="/login" className="text-primary font-medium hover:underline">Вернуться ко входу</Link>
        </p>
      </form>
    </div>
  ),
});
