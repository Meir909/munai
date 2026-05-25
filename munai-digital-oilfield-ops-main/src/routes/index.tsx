import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Droplets, Sparkles, Map, ShieldCheck, BarChart3, Mic } from "lucide-react";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "MUNAI — AI Digital Oilfield Operations Platform" },
      { name: "description", content: "MUNAI заменяет бумажные отчёты, Excel и устаревшие системы единой AI-платформой для нефтегазовых компаний." },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <header className="h-16 px-6 md:px-10 flex items-center border-b border-border bg-background/80 backdrop-blur sticky top-0 z-30">
        <Link to="/" className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-xl bg-primary grid place-items-center text-primary-foreground font-bold">M</div>
          <span className="font-bold tracking-tight text-lg">MUNAI</span>
        </Link>
        <nav className="ml-auto flex items-center gap-2">
          <Link to="/login"><Button variant="ghost">Войти</Button></Link>
          <Link to="/register"><Button>Начать</Button></Link>
        </nav>
      </header>

      <section className="munai-grad px-6 md:px-10 pt-20 pb-24">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 text-xs font-medium uppercase tracking-wider px-3 py-1.5 rounded-full bg-accent text-accent-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" /> AI Digital Oilfield Platform
          </div>
          <h1 className="mt-6 text-5xl md:text-7xl font-bold tracking-tight leading-[1.05]">
            Один экран. <br className="hidden md:block" />
            <span className="text-primary">Весь промысел.</span>
          </h1>
          <p className="mt-6 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
            MUNAI заменяет бумажные журналы, Excel и устаревшие системы единой AI-платформой
            для управления скважинами, отчётами и операционной аналитикой.
          </p>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Link to="/app/dashboard">
              <Button size="lg" className="h-12 px-7 text-base">
                Открыть демо <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="h-12 px-7 text-base">Войти в систему</Button>
            </Link>
          </div>
          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
            {[
              { v: "−87%", l: "ручного ввода" },
              { v: "3×", l: "быстрее отчёты" },
              { v: "24/7", l: "AI-мониторинг" },
              { v: "100%", l: "аудит-история" },
            ].map((s) => (
              <div key={s.l} className="rounded-2xl border border-border bg-card p-4">
                <div className="text-3xl font-bold text-primary">{s.v}</div>
                <div className="text-xs text-muted-foreground mt-1">{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 md:px-10 py-20 border-t border-border">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center">Что умеет MUNAI</h2>
          <p className="text-center text-muted-foreground mt-3 max-w-xl mx-auto">
            Простой интерфейс для оператора в поле и мощная аналитика для руководителя в офисе.
          </p>
          <div className="mt-12 grid md:grid-cols-3 gap-5">
            {[
              { icon: Mic, t: "Голосовые отчёты", d: "Оператор диктует параметры — MUNAI сам заполняет форму. Никакой бумаги." },
              { icon: Sparkles, t: "AI-валидация", d: "Каждый отчёт проверяется на аномалии и ошибки до того, как попадёт к менеджеру." },
              { icon: Map, t: "Карта скважин", d: "Все скважины региона на одной карте с цветовой индикацией статуса в реальном времени." },
              { icon: Droplets, t: "Управление скважинами", d: "Параметры, история, замеры — всё в одном месте, доступно с телефона." },
              { icon: ShieldCheck, t: "Согласования", d: "Менеджер и директор подтверждают отчёты в один клик. Полный аудит-журнал." },
              { icon: BarChart3, t: "KPI и аналитика", d: "Дашборды для руководства: добыча, эффективность, простои, тренды." },
            ].map((f) => (
              <div key={f.t} className="rounded-2xl border border-border bg-card p-6 hover:shadow-elevated transition">
                <div className="h-11 w-11 rounded-xl bg-accent grid place-items-center">
                  <f.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="mt-4 text-lg font-semibold">{f.t}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground leading-relaxed">{f.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 md:px-10 py-20 border-t border-border bg-muted/30">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold">Готовы увидеть MUNAI в действии?</h2>
          <p className="mt-3 text-muted-foreground">Демо доступно без регистрации — переключайтесь между ролями.</p>
          <Link to="/app/dashboard"><Button size="lg" className="mt-7 h-12 px-7">Запустить демо</Button></Link>
        </div>
      </section>

      <footer className="px-6 md:px-10 py-8 border-t border-border text-sm text-muted-foreground flex flex-wrap items-center justify-between gap-2">
        <div>© 2026 MUNAI. AI Digital Oilfield Operations Platform.</div>
        <div className="flex gap-4">
          <Link to="/login">Войти</Link>
          <Link to="/register">Регистрация</Link>
        </div>
      </footer>
    </div>
  );
}
