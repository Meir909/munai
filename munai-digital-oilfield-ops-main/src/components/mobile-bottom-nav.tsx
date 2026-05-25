import { Link, useRouterState } from "@tanstack/react-router";
import { LayoutDashboard, Droplets, Map, FileText, Bell } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export function MobileBottomNav() {
  const { t } = useI18n();
  const path = useRouterState({ select: (r) => r.location.pathname });
  const items = [
    { to: "/app/dashboard", label: t("dashboard"), icon: LayoutDashboard },
    { to: "/app/wells", label: t("wells"), icon: Droplets },
    { to: "/app/reports/new", label: t("new_report"), icon: FileText, accent: true },
    { to: "/app/map", label: t("map"), icon: Map },
    { to: "/app/notifications", label: t("notifications"), icon: Bell },
  ];
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-card border-t border-border h-16 flex items-stretch">
      {items.map((i) => {
        const active = path.startsWith(i.to);
        const Icon = i.icon;
        return (
          <Link
            key={i.to}
            to={i.to}
            className={cn(
              "flex-1 flex flex-col items-center justify-center gap-0.5 text-[10px] font-medium",
              i.accent && "relative",
              active ? "text-primary" : "text-muted-foreground",
            )}
          >
            {i.accent ? (
              <div className="absolute -top-5 h-12 w-12 rounded-full bg-primary text-primary-foreground grid place-items-center shadow-elevated">
                <Icon className="h-6 w-6" />
              </div>
            ) : (
              <Icon className="h-5 w-5" />
            )}
            <span className={cn(i.accent && "mt-7")}>{i.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
