// MUNAI mock data layer — entirely client-side for the UI demo MVP.

export type Role = "operator" | "manager" | "director" | "admin";

export interface DemoUser {
  id: string;
  name: string;
  role: Role;
  email: string;
  position: string;
  region: string;
}

export const demoUsers: Record<Role, DemoUser> = {
  operator: {
    id: "u-op-01",
    name: "Айбек Сарсенов",
    role: "operator",
    email: "operator@munai.kz",
    position: "Оператор по добыче нефти",
    region: "Месторождение Узень-3",
  },
  manager: {
    id: "u-mg-01",
    name: "Дана Жумабекова",
    role: "manager",
    email: "manager@munai.kz",
    position: "Менеджер участка",
    region: "Участок Северный",
  },
  director: {
    id: "u-dr-01",
    name: "Ержан Касымов",
    role: "director",
    email: "director@munai.kz",
    position: "Директор по добыче",
    region: "Регион Мангистау",
  },
  admin: {
    id: "u-ad-01",
    name: "Админ Системы",
    role: "admin",
    email: "admin@munai.kz",
    position: "Системный администратор",
    region: "HQ",
  },
};

export type WellStatus = "active" | "warning" | "inactive" | "broken";

export interface Well {
  id: string;
  code: string;
  name: string;
  status: WellStatus;
  product: "oil" | "gas" | "condensate";
  production24h: number; // m3
  temperature: number; // °C
  tubingInternalP: number; // atm
  tubingExternalP: number;
  annulusP: number;
  pumpStrokes: number; // per minute
  lat: number; // 0-100 (relative map)
  lng: number;
  operatorId: string;
  managerId: string;
  lastReport: string;
}

const rand = (min: number, max: number) => +(Math.random() * (max - min) + min).toFixed(1);

const statuses: WellStatus[] = ["active", "active", "active", "warning", "inactive", "broken"];

export const wells: Well[] = Array.from({ length: 24 }).map((_, i) => ({
  id: `w-${i + 1}`,
  code: `UZ-${(101 + i).toString()}`,
  name: `Скважина №${101 + i}`,
  status: statuses[i % statuses.length],
  product: i % 5 === 0 ? "gas" : i % 7 === 0 ? "condensate" : "oil",
  production24h: rand(8, 78),
  temperature: rand(38, 92),
  tubingInternalP: rand(45, 180),
  tubingExternalP: rand(20, 90),
  annulusP: rand(2, 18),
  pumpStrokes: Math.round(rand(4, 9)),
  lat: 12 + ((i * 37) % 76),
  lng: 8 + ((i * 53) % 84),
  operatorId: i % 2 === 0 ? "u-op-01" : "u-op-02",
  managerId: "u-mg-01",
  lastReport: `${(i % 12) + 1}ч назад`,
}));

export interface Report {
  id: string;
  wellCode: string;
  operator: string;
  createdAt: string;
  status: "pending" | "approved" | "flagged" | "rejected";
  aiScore: number; // 0-100
  summary: string;
  flag?: string;
}

export const reports: Report[] = [
  { id: "r-1", wellCode: "UZ-101", operator: "Айбек С.", createdAt: "Сегодня, 09:14", status: "pending", aiScore: 92, summary: "Параметры в норме, добыча стабильна." },
  { id: "r-2", wellCode: "UZ-104", operator: "Айбек С.", createdAt: "Сегодня, 08:02", status: "flagged", aiScore: 41, summary: "Температура выше нормы на 12%.", flag: "Аномалия температуры" },
  { id: "r-3", wellCode: "UZ-108", operator: "Нурлан Т.", createdAt: "Вчера, 18:30", status: "approved", aiScore: 96, summary: "Замер давления выполнен корректно." },
  { id: "r-4", wellCode: "UZ-112", operator: "Айбек С.", createdAt: "Вчера, 16:11", status: "approved", aiScore: 88, summary: "Стандартный суточный замер." },
  { id: "r-5", wellCode: "UZ-117", operator: "Нурлан Т.", createdAt: "Вчера, 12:45", status: "rejected", aiScore: 22, summary: "Нечитаемый файл, требуется повторная подача.", flag: "Низкое качество данных" },
  { id: "r-6", wellCode: "UZ-120", operator: "Айбек С.", createdAt: "2 дня назад", status: "approved", aiScore: 94, summary: "Все параметры в пределах нормы." },
  { id: "r-7", wellCode: "UZ-122", operator: "Айбек С.", createdAt: "2 дня назад", status: "pending", aiScore: 78, summary: "Зафиксировано падение пластового давления." },
];

export const notifications = [
  { id: "n-1", icon: "alert", title: "AI: Аномалия на UZ-104", body: "Температура выше нормы на 12%. Требуется проверка.", time: "5 мин назад", unread: true, tone: "warning" as const },
  { id: "n-2", icon: "check", title: "Отчёт одобрен", body: "Отчёт по UZ-108 одобрен менеджером.", time: "1 ч назад", unread: true, tone: "success" as const },
  { id: "n-3", icon: "calendar", title: "Событие в календаре", body: "Плановое совещание 26 мая в 10:00.", time: "3 ч назад", unread: false, tone: "info" as const },
  { id: "n-4", icon: "edit", title: "Запрос на доработку", body: "Отчёт UZ-117 отклонён, требуется повтор.", time: "Вчера", unread: false, tone: "destructive" as const },
];

export const calendarEvents = [
  { id: "e-1", title: "Плановый осмотр UZ-104", date: "26 мая, 10:00", type: "Осмотр" },
  { id: "e-2", title: "Совещание менеджеров", date: "27 мая, 14:00", type: "Совещание" },
  { id: "e-3", title: "Тренинг по безопасности", date: "29 мая, 09:00", type: "Обучение" },
  { id: "e-4", title: "Отчёт за месяц — дедлайн", date: "31 мая, 18:00", type: "Дедлайн" },
];

export const trainings = [
  { id: "t-1", title: "Основы работы оператора", duration: "12 мин", progress: 100 },
  { id: "t-2", title: "Как подавать отчёт через MUNAI", duration: "8 мин", progress: 65 },
  { id: "t-3", title: "Голосовой ввод и AI-ассистент", duration: "6 мин", progress: 30 },
  { id: "t-4", title: "Техника безопасности на скважине", duration: "20 мин", progress: 0 },
];

export const productionTrend = [
  { day: "Пн", oil: 420, gas: 180 },
  { day: "Вт", oil: 440, gas: 192 },
  { day: "Ср", oil: 410, gas: 175 },
  { day: "Чт", oil: 468, gas: 198 },
  { day: "Пт", oil: 482, gas: 210 },
  { day: "Сб", oil: 471, gas: 205 },
  { day: "Вс", oil: 495, gas: 218 },
];

export const auditLog = [
  { id: "a-1", who: "Дана Ж. (manager)", action: "Одобрила отчёт", target: "UZ-108", time: "Сегодня 10:12" },
  { id: "a-2", who: "Айбек С. (operator)", action: "Создал отчёт", target: "UZ-101", time: "Сегодня 09:14" },
  { id: "a-3", who: "Ержан К. (director)", action: "Изменил статус скважины", target: "UZ-117 → broken", time: "Вчера 17:40" },
  { id: "a-4", who: "AI Engine", action: "Отметил аномалию", target: "UZ-104", time: "Вчера 16:00" },
  { id: "a-5", who: "Админ", action: "Создал пользователя", target: "operator+02@munai.kz", time: "3 дня назад" },
];

export const allUsersAdmin = [
  { id: "u-1", name: "Айбек Сарсенов", role: "operator", email: "operator@munai.kz", active: true },
  { id: "u-2", name: "Нурлан Темиров", role: "operator", email: "n.temirov@munai.kz", active: true },
  { id: "u-3", name: "Дана Жумабекова", role: "manager", email: "manager@munai.kz", active: true },
  { id: "u-4", name: "Ержан Касымов", role: "director", email: "director@munai.kz", active: true },
  { id: "u-5", name: "Алия Жакупова", role: "operator", email: "a.zhakupova@munai.kz", active: false },
];
