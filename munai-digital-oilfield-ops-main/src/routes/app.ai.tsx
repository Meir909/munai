import { createFileRoute } from "@tanstack/react-router";
import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sparkles, Send, Bot, User, AlertTriangle, TrendingDown, Activity, Loader2 } from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { aiApi } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/app/ai")({
  head: () => ({ meta: [{ title: "AI-аналитика — MUNAI" }] }),
  component: AIPage,
});

function AIPage() {
  const [messages, setMessages] = useState<{ role: "user" | "ai"; text: string }[]>([
    { role: "ai", text: "Здравствуйте! Я — AI-ассистент MUNAI. Спросите меня про скважины, отчёты или производство." },
  ]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: insights } = useQuery({
    queryKey: ["ai-insights"],
    queryFn: aiApi.insights,
  });

  const chatMutation = useMutation({
    mutationFn: (msg: string) => aiApi.chat(msg),
    onSuccess: (data) => {
      setMessages((m) => [...m, { role: "ai", text: data.reply }]);
    },
    onError: (e: Error) => {
      toast.error(e.message);
      setMessages((m) => [...m, { role: "ai", text: "Произошла ошибка. Попробуйте снова." }]);
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || chatMutation.isPending) return;
    const text = input.trim();
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    chatMutation.mutate(text);
  };

  const insightData = insights?.insights as Array<{ tone: string; title: string; desc: string }> ?? [
    { tone: "warning", title: "3 аномалии", desc: "Обнаружены за последние 24 часа" },
    { tone: "destructive", title: "UZ-117 — риск останова", desc: "Падение давления −18% за неделю" },
    { tone: "info", title: "Эффективность +8%", desc: "По сравнению с прошлой неделей" },
  ];

  const suggestions = insights?.suggestions as string[] ?? [];

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-5">
      <div>
        <h1 className="text-3xl md:text-4xl font-bold flex items-center gap-2">
          <Sparkles className="h-8 w-8 text-primary" /> AI-аналитика
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Интеллектуальный анализ производства и рисков</p>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {insightData.map((ins, i) => (
          <InsightCard
            key={i}
            icon={i === 0 ? AlertTriangle : i === 1 ? TrendingDown : Activity}
            tone={ins.tone as "warning" | "destructive" | "info"}
            title={ins.title}
            desc={ins.desc}
          />
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 rounded-2xl border border-border bg-card flex flex-col h-[520px]">
          <div className="p-4 border-b border-border flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary grid place-items-center"><Bot className="h-4 w-4 text-primary-foreground" /></div>
            <div>
              <div className="font-semibold text-sm">AI-ассистент MUNAI</div>
              <div className="text-xs text-muted-foreground">{chatMutation.isPending ? "Думаю…" : "Онлайн · отвечает за секунды"}</div>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : ""}`}>
                {m.role === "ai" && <div className="h-7 w-7 rounded-full bg-accent grid place-items-center shrink-0"><Bot className="h-4 w-4 text-primary" /></div>}
                <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                  {m.text}
                </div>
                {m.role === "user" && <div className="h-7 w-7 rounded-full bg-primary grid place-items-center shrink-0"><User className="h-4 w-4 text-primary-foreground" /></div>}
              </div>
            ))}
            {chatMutation.isPending && (
              <div className="flex gap-2">
                <div className="h-7 w-7 rounded-full bg-accent grid place-items-center shrink-0"><Bot className="h-4 w-4 text-primary" /></div>
                <div className="bg-muted rounded-2xl px-4 py-2.5 flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Анализирую данные…</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <form onSubmit={send} className="p-3 border-t border-border flex gap-2">
            <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Спросите AI…" className="h-11" disabled={chatMutation.isPending} />
            <Button type="submit" className="h-11" disabled={chatMutation.isPending || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>

        <div className="rounded-2xl border border-border bg-card p-5 space-y-4">
          <h3 className="font-semibold">Рекомендации AI</h3>
          {(suggestions.length > 0 ? suggestions : [
            "Перепроверить замер на UZ-104 — температура аномальная",
            "Запланировать ТО для UZ-117 в течение недели",
            "Обновить параметры насоса на UZ-122",
            "Обучить оператора новой форме отчёта",
          ]).map((rec, i) => (
            <button
              key={i}
              className="w-full text-left rounded-xl border border-border p-3 text-sm hover:border-primary hover:bg-accent transition"
              onClick={() => { setInput(rec); }}
            >
              <div className="flex items-start gap-2">
                <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                {rec}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function InsightCard({ icon: Icon, tone, title, desc }: { icon: React.ElementType; tone: "warning" | "destructive" | "info"; title: string; desc: string }) {
  const cls = tone === "warning" ? "bg-warning/15 text-warning-foreground" : tone === "destructive" ? "bg-destructive/10 text-destructive" : "bg-info/10 text-info";
  return (
    <div className="rounded-2xl border border-border bg-card p-5">
      <div className={`h-10 w-10 rounded-xl grid place-items-center ${cls}`}><Icon className="h-5 w-5" /></div>
      <div className="mt-3 font-semibold">{title}</div>
      <div className="text-xs text-muted-foreground mt-0.5">{desc}</div>
    </div>
  );
}
