import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import {
  LayoutDashboard, Droplets, Map, FileText, ShieldCheck, Sparkles, BarChart3,
  Bell, CalendarDays, GraduationCap, UserCircle, Settings, ShieldAlert, History, LogOut,
} from "lucide-react";
import { useI18n, type TKey } from "@/lib/i18n";
import { useSession } from "@/lib/session";
import type { Role } from "@/lib/session";
import { cn } from "@/lib/utils";
import { useAuthStore, useNotifStore } from "@/lib/store";
import { toast } from "sonner";

type Item = { to: string; key: TKey; icon: React.ElementType; roles: Role[] };

const NAV: Item[] = [
  { to: "/app/dashboard", key: "dashboard", icon: LayoutDashboard, roles: ["operator", "manager", "director", "admin"] },
  { to: "/app/wells", key: "wells", icon: Droplets, roles: ["operator", "manager", "director", "admin"] },
  { to: "/app/map", key: "map", icon: Map, roles: ["operator", "manager", "director", "admin"] },
  { to: "/app/reports", key: "reports", icon: FileText, roles: ["operator", "manager", "director", "admin"] },
  { to: "/app/approvals", key: "approvals", icon: ShieldCheck, roles: ["manager", "director"] },
  { to: "/app/ai", key: "ai_center", icon: Sparkles, roles: ["operator", "manager", "director", "admin"] },
  { to: "/app/kpi", key: "kpi", icon: BarChart3, roles: ["manager", "director", "admin"] },
  { to: "/app/calendar", key: "calendar", icon: CalendarDays, roles: ["operator", "manager", "director", "admin"] },
  { to: "/app/training", key: "training", icon: GraduationCap, roles: ["operator", "manager", "director", "admin"] },
  { to: "/app/notifications", key: "notifications", icon: Bell, roles: ["operator", "manager", "director", "admin"] },
  { to: "/app/admin", key: "admin", icon: ShieldAlert, roles: ["admin"] },
  { to: "/app/audit", key: "audit", icon: History, roles: ["manager", "director", "admin"] },
];

export function AppSidebar() {
  const { t } = useI18n();
  const { role } = useSession();
  const { clearAuth } = useAuthStore();
  const { unreadCount } = useNotifStore();
  const nav = useNavigate();
  const path = useRouterState({ select: (r) => r.location.pathname });
  const items = NAV.filter((i) => i.roles.includes(role));
  const notifCount = unreadCount();

  const handleLogout = () => {
    clearAuth();
    toast.success("Вы вышли из системы");
    nav({ to: "/login" });
  };

  return (
    <aside className="hidden md:flex w-64 shrink-0 flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border">
      <div className="px-5 py-5 flex items-center gap-2 border-b border-sidebar-border">
        <div className="h-9 w-9 rounded-xl bg-primary grid place-items-center text-primary-foreground font-bold">M</div>
        <div>
          <div className="text-base font-bold tracking-tight">MUNAI</div>
          <div className="text-[11px] uppercase tracking-wider text-sidebar-foreground/60">Digital Oilfield</div>
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
        {items.map((i) => {
          const active = path.startsWith(i.to);
          const Icon = i.icon;
          return (
            <Link
              key={i.to}
              to={i.to}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition",
                active
                  ? "bg-primary text-primary-foreground shadow-soft"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              )}
            >
              <Icon className="h-5 w-5 shrink-0" />
              <span className="flex-1">{t(i.key)}</span>
              {i.to === "/app/notifications" && notifCount > 0 && (
                <span className="h-5 w-5 rounded-full bg-primary text-primary-foreground text-[10px] font-bold grid place-items-center">{notifCount > 9 ? "9+" : notifCount}</span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="px-2 pb-3 pt-2 border-t border-sidebar-border space-y-0.5">
        <Link to="/app/profile" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground/80 hover:bg-sidebar-accent">
          <UserCircle className="h-5 w-5" /> {t("profile")}
        </Link>
        <Link to="/app/settings" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground/80 hover:bg-sidebar-accent">
          <Settings className="h-5 w-5" /> {t("settings")}
        </Link>
        <button onClick={handleLogout} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-sidebar-foreground/80 hover:bg-sidebar-accent text-left">
          <LogOut className="h-5 w-5" /> {t("logout")}
        </button>
      </div>
    </aside>
  );
}
