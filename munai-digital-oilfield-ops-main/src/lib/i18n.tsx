import { createContext, useContext, useState, type ReactNode } from "react";

export type Lang = "ru" | "kz" | "en";

const dict = {
  ru: {
    app_name: "MUNAI",
    tagline: "AI-платформа цифрового промысла",
    dashboard: "Главная",
    wells: "Скважины",
    map: "Карта скважин",
    reports: "Отчёты",
    new_report: "Новый отчёт",
    approvals: "Согласования",
    ai_center: "AI-аналитика",
    kpi: "KPI",
    notifications: "Уведомления",
    calendar: "Календарь",
    training: "Обучение",
    profile: "Профиль",
    settings: "Настройки",
    admin: "Админ-панель",
    audit: "Журнал действий",
    logout: "Выйти",
    login: "Войти",
    register: "Регистрация",
    forgot: "Забыли пароль?",
    welcome: "Добро пожаловать",
    quick_actions: "Быстрые действия",
    view_all: "Смотреть все",
    operator: "Оператор",
    manager: "Менеджер",
    director: "Директор",
    role_admin: "Администратор",
  },
  kz: {
    app_name: "MUNAI",
    tagline: "Цифрлық кәсіпшіліктің AI-платформасы",
    dashboard: "Басты бет",
    wells: "Ұңғымалар",
    map: "Ұңғымалар картасы",
    reports: "Есептер",
    new_report: "Жаңа есеп",
    approvals: "Бекіту",
    ai_center: "AI-талдау",
    kpi: "KPI",
    notifications: "Хабарландырулар",
    calendar: "Күнтізбе",
    training: "Оқыту",
    profile: "Профиль",
    settings: "Баптаулар",
    admin: "Әкімші панелі",
    audit: "Іс-әрекеттер журналы",
    logout: "Шығу",
    login: "Кіру",
    register: "Тіркелу",
    forgot: "Құпиясөзді ұмыттыңыз ба?",
    welcome: "Қош келдіңіз",
    quick_actions: "Жылдам әрекеттер",
    view_all: "Барлығын көру",
    operator: "Оператор",
    manager: "Менеджер",
    director: "Директор",
    role_admin: "Әкімші",
  },
  en: {
    app_name: "MUNAI",
    tagline: "AI Digital Oilfield Operations Platform",
    dashboard: "Dashboard",
    wells: "Wells",
    map: "Well Map",
    reports: "Reports",
    new_report: "New Report",
    approvals: "Approvals",
    ai_center: "AI Center",
    kpi: "KPI",
    notifications: "Notifications",
    calendar: "Calendar",
    training: "Training",
    profile: "Profile",
    settings: "Settings",
    admin: "Admin Panel",
    audit: "Audit Log",
    logout: "Log out",
    login: "Sign in",
    register: "Sign up",
    forgot: "Forgot password?",
    welcome: "Welcome",
    quick_actions: "Quick actions",
    view_all: "View all",
    operator: "Operator",
    manager: "Manager",
    director: "Director",
    role_admin: "Administrator",
  },
} as const;

export type TKey = keyof (typeof dict)["ru"];

const I18nCtx = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: (k: TKey) => string }>({
  lang: "ru",
  setLang: () => {},
  t: (k) => k,
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("ru");
  const t = (k: TKey) => dict[lang][k] ?? k;
  return <I18nCtx.Provider value={{ lang, setLang, t }}>{children}</I18nCtx.Provider>;
}

export const useI18n = () => useContext(I18nCtx);
