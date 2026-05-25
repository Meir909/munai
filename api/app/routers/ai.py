from fastapi import APIRouter, Depends
from sqlite3 import Connection
from app.database import get_db
from app import schemas
from app.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])

_RESPONSES = {
    ("скважин", "well"): ("На платформе {n} скважин. {active} активных, {warning} требуют внимания.", ["Показать карту скважин", "Отчёты по скважинам"]),
    ("добыч", "production"): ("Суммарная суточная добыча составляет {production:.0f} т/сут. Тренд стабильный.", ["Показать KPI дашборд", "Детализация по скважинам"]),
    ("отчёт", "report"): ("Ожидают проверки {pending} отчётов. {flagged} помечены AI как аномальные.", ["Перейти к согласованиям", "Создать новый отчёт"]),
    ("темпер", "temperat"): ("Высокая температура — признак проблем с пластом. Проверьте скважины со статусом 'warning'.", ["Карта скважин", "Список отчётов"]),
    ("аномал", "anomal"): ("AI выявил {flagged} аномалий. Рекомендую срочно проверить соответствующие скважины.", ["Согласования", "Карта скважин"]),
    ("привет", "hello", "hi", "здравствуй"): ("Привет! Я AI-ассистент MUNAI. Спрошу о скважинах, добыче, отчётах или аномалиях.", ["Статистика добычи", "Статус скважин", "Ожидающие отчёты"]),
}

_DEFAULT = ("Я обрабатываю данные платформы MUNAI. Спросите о скважинах, добыче, отчётах или аномалиях.", ["Статистика добычи", "Статус скважин"])


@router.post("/chat", response_model=schemas.AIChatResponse)
def chat(body: schemas.AIChatRequest, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    msg = body.message.lower()
    n_wells = db.execute("SELECT COUNT(*) FROM wells").fetchone()[0]
    active = db.execute("SELECT COUNT(*) FROM wells WHERE status='active'").fetchone()[0]
    warning = db.execute("SELECT COUNT(*) FROM wells WHERE status='warning'").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM reports WHERE status='pending'").fetchone()[0]
    flagged = db.execute("SELECT COUNT(*) FROM reports WHERE status='flagged'").fetchone()[0]
    production = db.execute("SELECT COALESCE(SUM(production24h),0) FROM wells WHERE status='active'").fetchone()[0]

    for keys, (template, suggestions) in _RESPONSES.items():
        if any(k in msg for k in keys):
            reply = template.format(n=n_wells, active=active, warning=warning, pending=pending, flagged=flagged, production=production)
            return schemas.AIChatResponse(reply=reply, suggestions=suggestions)

    return schemas.AIChatResponse(reply=_DEFAULT[0], suggestions=list(_DEFAULT[1]))


@router.get("/insights")
def insights(db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    warning = db.execute("SELECT COUNT(*) FROM wells WHERE status='warning'").fetchone()[0]
    flagged = db.execute("SELECT COUNT(*) FROM reports WHERE status='flagged'").fetchone()[0]
    return {
        "insights": [
            {"type": "warning", "message": f"{warning} скважин требуют внимания"},
            {"type": "info", "message": f"{flagged} отчётов помечены AI"},
        ]
    }
