import { Bell, Moon, Sun, Globe, LogOut } from "lucide-react";
import { useI18n, type Lang } from "@/lib/i18n";
import { useTheme } from "@/lib/theme";
import { useSession } from "@/lib/session";
import type { Role } from "@/lib/session";
import { Link, useNavigate } from "@tanstack/react-router";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { useAuthStore, useNotifStore } from "@/lib/store";
import { toast } from "sonner";

const langs: { code: Lang; label: string }[] = [
  { code: "ru", label: "RU" },
  { code: "kz", label: "KZ" },
  { code: "en", label: "EN" },
];

const roleLabels: Record<Role, string> = {
  operator: "Оператор",
  manager: "Менеджер",
  director: "Директор",
  admin: "Администратор",
};

export function TopBar() {
  const { lang, setLang } = useI18n();
  const { theme, toggle } = useTheme();
  const { user, role } = useSession();
  const { clearAuth } = useAuthStore();
  const { unreadCount } = useNotifStore();
  const nav = useNavigate();
  const unread = unreadCount();

  const handleLogout = () => {
    clearAuth();
    toast.success("Вы вышли из системы");
    nav({ to: "/login" });
  };

  return (
    <header className="h-16 border-b border-border bg-card/80 backdrop-blur flex items-center px-4 md:px-6 gap-3 sticky top-0 z-30">
      <div className="md:hidden font-bold text-lg">MUNAI</div>

      <div className="ml-auto flex items-center gap-1.5">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Язык">
              <Globe className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {langs.map((l) => (
              <DropdownMenuItem key={l.code} onClick={() => setLang(l.code)} className={l.code === lang ? "font-semibold" : ""}>
                {l.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <Button variant="ghost" size="icon" onClick={toggle} aria-label="Тема">
          {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
        </Button>

        <Link to="/app/notifications" className="relative inline-flex">
          <Button variant="ghost" size="icon" aria-label="Уведомления">
            <Bell className="h-5 w-5" />
          </Button>
          {unread > 0 && (
            <span className="absolute top-1.5 right-1.5 h-4 w-4 grid place-items-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </Link>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 pl-2 pr-1 py-1 rounded-full hover:bg-muted transition">
              <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground grid place-items-center text-sm font-bold">
                {user.name.charAt(0)}
              </div>
              <div className="hidden sm:block text-left leading-tight pr-2">
                <div className="text-xs font-semibold">{user.name}</div>
                <div className="text-[10px] text-muted-foreground">{roleLabels[role]}</div>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuLabel>
              <div className="text-sm font-semibold">{user.name}</div>
              <div className="text-xs text-muted-foreground font-normal">{user.email}</div>
              <div className="text-xs text-muted-foreground font-normal mt-0.5">{roleLabels[role]}</div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild><Link to="/app/profile">Профиль</Link></DropdownMenuItem>
            <DropdownMenuItem asChild><Link to="/app/settings">Настройки</Link></DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
              <LogOut className="h-4 w-4 mr-2" /> Выйти
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
