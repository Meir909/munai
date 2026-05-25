import { cn } from "@/lib/utils";

type WellStatus = "active" | "warning" | "inactive" | "broken";
import { CheckCircle2, AlertTriangle, PauseCircle, XCircle, Clock, ShieldCheck, ShieldAlert, Flag } from "lucide-react";

export function StatusBadge({ status }: { status: WellStatus | "pending" | "approved" | "flagged" | "rejected" }) {
  const map: Record<string, { label: string; cls: string; icon: React.ElementType }> = {
    active:    { label: "Активна",      cls: "bg-success/10 text-success border-success/20", icon: CheckCircle2 },
    warning:   { label: "Внимание",     cls: "bg-warning/15 text-warning-foreground border-warning/30", icon: AlertTriangle },
    inactive:  { label: "Неактивна",    cls: "bg-muted text-muted-foreground border-border", icon: PauseCircle },
    broken:    { label: "Авария",       cls: "bg-destructive/10 text-destructive border-destructive/20", icon: XCircle },
    pending:   { label: "На проверке",  cls: "bg-info/10 text-info border-info/20", icon: Clock },
    approved:  { label: "Одобрено",     cls: "bg-success/10 text-success border-success/20", icon: ShieldCheck },
    flagged:   { label: "Аномалия",     cls: "bg-warning/15 text-warning-foreground border-warning/30", icon: Flag },
    rejected:  { label: "Отклонено",    cls: "bg-destructive/10 text-destructive border-destructive/20", icon: ShieldAlert },
  };
  const m = map[status];
  const Icon = m.icon;
  return (
    <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium", m.cls)}>
      <Icon className="h-3.5 w-3.5" /> {m.label}
    </span>
  );
}
