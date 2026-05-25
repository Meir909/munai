// Real auth session — reads from Zustand persisted store.
// Keeps backward-compatible useSession() hook so existing pages don't break.
import { createContext, useContext, type ReactNode } from "react";
import { useAuthStore } from "./store";

export type Role = "operator" | "manager" | "director" | "admin";

export interface DemoUser {
  id: string;
  name: string;
  role: Role;
  email: string;
  position: string;
  region: string;
}

interface SessionCtx {
  user: DemoUser;
  role: Role;
  isAuthenticated: boolean;
  setRole: (r: Role) => void; // kept for compat, no-op on real auth
}

const guest: DemoUser = {
  id: "",
  name: "Гость",
  role: "operator",
  email: "",
  position: "",
  region: "",
};

const Ctx = createContext<SessionCtx>({
  user: guest,
  role: "operator",
  isAuthenticated: false,
  setRole: () => {},
});

export function SessionProvider({ children }: { children: ReactNode }) {
  const { user } = useAuthStore();

  const sessionUser: DemoUser = user
    ? { id: user.id, name: user.name, role: user.role as Role, email: user.email, position: user.position, region: user.region }
    : guest;

  return (
    <Ctx.Provider value={{ user: sessionUser, role: sessionUser.role, isAuthenticated: !!user, setRole: () => {} }}>
      {children}
    </Ctx.Provider>
  );
}

export const useSession = () => useContext(Ctx);

// Also export demoUsers for any legacy references
export const demoUsers: Record<Role, DemoUser> = {
  operator: { id: "u-op-01", name: "Айбек Сарсенов", role: "operator", email: "operator@munai.kz", position: "Оператор по добыче нефти", region: "Месторождение Узень-3" },
  manager: { id: "u-mg-01", name: "Дана Жумабекова", role: "manager", email: "manager@munai.kz", position: "Менеджер участка", region: "Участок Северный" },
  director: { id: "u-dr-01", name: "Ержан Касымов", role: "director", email: "director@munai.kz", position: "Директор по добыче", region: "Регион Мангистау" },
  admin: { id: "u-ad-01", name: "Админ Системы", role: "admin", email: "admin@munai.kz", position: "Системный администратор", region: "HQ" },
};
