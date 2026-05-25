import { createFileRoute } from "@tanstack/react-router";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useI18n, type Lang } from "@/lib/i18n";
import { useTheme } from "@/lib/theme";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/app/settings")({
  head: () => ({ meta: [{ title: "Настройки — MUNAI" }] }),
  component: () => {
    const { lang, setLang } = useI18n();
    const { theme, toggle } = useTheme();
    return (
      <div className="p-4 md:p-8 max-w-2xl mx-auto space-y-5">
        <h1 className="text-3xl md:text-4xl font-bold">Настройки</h1>
        <div className="rounded-2xl border border-border bg-card p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <Label>Тёмная тема</Label>
              <p className="text-xs text-muted-foreground mt-0.5">Переключить визуальное оформление</p>
            </div>
            <Switch checked={theme === "dark"} onCheckedChange={toggle} />
          </div>
          <div>
            <Label className="mb-2 block">Язык интерфейса</Label>
            <div className="flex gap-2">
              {(["ru", "kz", "en"] as Lang[]).map((l) => (
                <Button key={l} variant={lang === l ? "default" : "outline"} onClick={() => setLang(l)} className="h-11 uppercase">{l}</Button>
              ))}
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>Push-уведомления</Label>
              <p className="text-xs text-muted-foreground mt-0.5">Получать уведомления о важных событиях</p>
            </div>
            <Switch defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>AI-валидация по умолчанию</Label>
              <p className="text-xs text-muted-foreground mt-0.5">Проверять все новые отчёты автоматически</p>
            </div>
            <Switch defaultChecked />
          </div>
        </div>
      </div>
    );
  },
});
