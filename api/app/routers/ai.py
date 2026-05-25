from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])

# Rule-based AI responses for the oilfield assistant
AI_RESPONSES = [
    ("uz-104", "На скважине UZ-104 зафиксирована аномалия температуры (+12% к норме). Рекомендую назначить плановый осмотр в ближайшие 24 часа."),
    ("uz-117", "UZ-117 показывает падение пластового давления −18% за неделю. Необходима диагностика насосного оборудования."),
    ("uz-122", "UZ-122: давление снизилось, рекомендуется проверить параметры насоса и обновить настройки."),
    ("аномал", "Обнаружены аномалии на 3 скважинах за последние 24 часа. Приоритет — UZ-104 (температура) и UZ-117 (давление)."),
    ("добыч", "Суммарная добыча за последние 7 дней составила около 3 186 м³. Эффективность выросла на 8.4% по сравнению с прошлой неделей."),
    ("отчёт", "Для создания отчёта перейдите в раздел «Отчёты» → «Новый отчёт». AI автоматически проверит параметры на аномалии."),
    ("насос", "Рекомендую проверить параметры насоса на скважинах с pump_strokes < 5 в минуту — это может указывать на износ."),
    ("давлен", "Мониторинг давления: нормальный диапазон P НКТ — 45–160 атм. Превышение требует немедленного внимания."),
    ("температур", "Нормальный диапазон температуры на устье скважины — 38–80°C. Значения выше 90°C считаются аномальными."),
]

DEFAULT_RESPONSES = [
    "Я анализирую данные по всем скважинам в режиме реального времени. Уточните ваш вопрос — по какой скважине или показателю нужна информация?",
    "На основе текущих данных все ключевые параметры в норме, кроме UZ-104 (температура) и UZ-117 (давление). Рекомендую проверить эти объекты.",
    "Я готов помочь с анализом производительности, выявлением аномалий и рекомендациями по обслуживанию. Задайте конкретный вопрос.",
]

AI_SUGGESTIONS = [
    "Перепроверить замер на UZ-104 — температура аномальная",
    "Запланировать ТО для UZ-117 в течение недели",
    "Обновить параметры насоса на UZ-122",
    "Проверить скважины с добычей ниже 15 м³/сутки",
]

AI_INSIGHTS = [
    {"icon": "AlertTriangle", "tone": "warning", "title": "3 аномалии", "desc": "Обнаружены за последние 24 часа"},
    {"icon": "TrendingDown", "tone": "destructive", "title": "UZ-117 — риск останова", "desc": "Падение давления −18% за неделю"},
    {"icon": "Activity", "tone": "info", "title": "Эффективность +8%", "desc": "По сравнению с прошлой неделей"},
]


@router.post("/chat", response_model=schemas.AIChatResponse)
def ai_chat(
    body: schemas.AIChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    msg_lower = body.message.lower()
    reply = None
    for keyword, response in AI_RESPONSES:
        if keyword in msg_lower:
            reply = response
            break

    if not reply:
        import random
        reply = random.choice(DEFAULT_RESPONSES)

    return schemas.AIChatResponse(reply=reply, suggestions=AI_SUGGESTIONS)


@router.get("/insights")
def ai_insights(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    anomaly_count = db.query(models.Report).filter(models.Report.status == "flagged").count()
    return {
        "insights": [
            {"tone": "warning", "title": f"{anomaly_count} аномалий", "desc": "Обнаружены за последние 24 часа"},
            {"tone": "destructive", "title": "UZ-117 — риск останова", "desc": "Падение давления −18% за неделю"},
            {"tone": "info", "title": "Эффективность +8%", "desc": "По сравнению с прошлой неделей"},
        ],
        "suggestions": AI_SUGGESTIONS,
    }
