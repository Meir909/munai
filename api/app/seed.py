"""Seed the database with demo data matching the frontend mock."""
import uuid
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from app import models
from app.auth import hash_password


def seed_db(db: Session):
    if db.query(models.User).count() > 0:
        return  # already seeded

    # ── Users ────────────────────────────────────────────────────────────────
    users_data = [
        {"id": "u-op-01", "name": "Айбек Сарсенов", "email": "operator@munai.kz", "role": "operator", "position": "Оператор по добыче нефти", "region": "Месторождение Узень-3"},
        {"id": "u-op-02", "name": "Нурлан Темиров", "email": "n.temirov@munai.kz", "role": "operator", "position": "Оператор по добыче нефти", "region": "Месторождение Узень-3"},
        {"id": "u-mg-01", "name": "Дана Жумабекова", "email": "manager@munai.kz", "role": "manager", "position": "Менеджер участка", "region": "Участок Северный"},
        {"id": "u-dr-01", "name": "Ержан Касымов", "email": "director@munai.kz", "role": "director", "position": "Директор по добыче", "region": "Регион Мангистау"},
        {"id": "u-ad-01", "name": "Админ Системы", "email": "admin@munai.kz", "role": "admin", "position": "Системный администратор", "region": "HQ"},
        {"id": "u-op-03", "name": "Алия Жакупова", "email": "a.zhakupova@munai.kz", "role": "operator", "position": "Оператор по добыче нефти", "region": "Месторождение Узень-2", "active": False},
    ]
    users = {}
    for ud in users_data:
        u = models.User(
            id=ud["id"],
            name=ud["name"],
            email=ud["email"],
            hashed_password=hash_password("demo"),
            role=ud["role"],
            position=ud.get("position", ""),
            region=ud.get("region", ""),
            active=ud.get("active", True),
        )
        db.add(u)
        users[ud["id"]] = u
    db.flush()

    # ── Wells ─────────────────────────────────────────────────────────────────
    statuses = ["active", "active", "active", "warning", "inactive", "broken"]
    well_objects = []
    for i in range(24):
        st = statuses[i % len(statuses)]
        product = "gas" if i % 5 == 0 else "condensate" if i % 7 == 0 else "oil"
        w = models.Well(
            id=f"w-{i+1}",
            code=f"UZ-{101+i}",
            name=f"Скважина №{101+i}",
            status=st,
            product=product,
            production24h=round(random.uniform(8, 78), 1),
            temperature=round(random.uniform(38, 92), 1),
            tubing_internal_p=round(random.uniform(45, 180), 1),
            tubing_external_p=round(random.uniform(20, 90), 1),
            annulus_p=round(random.uniform(2, 18), 1),
            pump_strokes=random.randint(4, 9),
            lat=round(52.0 + (i * 0.15) % 3.0, 4),
            lng=round(52.0 + (i * 0.23) % 5.0, 4),
            operator_id="u-op-01" if i % 2 == 0 else "u-op-02",
            manager_id="u-mg-01",
        )
        db.add(w)
        well_objects.append(w)
    db.flush()

    # ── Reports ───────────────────────────────────────────────────────────────
    report_seeds = [
        {"id": "r-1", "well_id": "w-1", "operator_id": "u-op-01", "status": "pending", "ai_score": 92,
         "summary": "Параметры в норме, добыча стабильна.", "temperature": 72.0, "production24h": 45.0,
         "tubing_internal_p": 120.0, "tubing_external_p": 55.0, "annulus_p": 8.0, "pump_strokes": 6,
         "created_at": datetime.utcnow() - timedelta(hours=2)},
        {"id": "r-2", "well_id": "w-4", "operator_id": "u-op-01", "status": "flagged", "ai_score": 41,
         "summary": "Температура выше нормы на 12%.", "flag": "Аномалия температуры",
         "temperature": 96.0, "production24h": 38.0, "tubing_internal_p": 135.0,
         "tubing_external_p": 60.0, "annulus_p": 10.0, "pump_strokes": 5,
         "created_at": datetime.utcnow() - timedelta(hours=3)},
        {"id": "r-3", "well_id": "w-8", "operator_id": "u-op-02", "status": "approved", "ai_score": 96,
         "summary": "Замер давления выполнен корректно.", "temperature": 68.0, "production24h": 52.0,
         "tubing_internal_p": 115.0, "tubing_external_p": 50.0, "annulus_p": 7.0, "pump_strokes": 7,
         "created_at": datetime.utcnow() - timedelta(days=1, hours=5)},
        {"id": "r-4", "well_id": "w-12", "operator_id": "u-op-01", "status": "approved", "ai_score": 88,
         "summary": "Стандартный суточный замер.", "temperature": 74.0, "production24h": 41.0,
         "tubing_internal_p": 118.0, "tubing_external_p": 53.0, "annulus_p": 9.0, "pump_strokes": 6,
         "created_at": datetime.utcnow() - timedelta(days=1, hours=7)},
        {"id": "r-5", "well_id": "w-17", "operator_id": "u-op-02", "status": "rejected", "ai_score": 22,
         "summary": "Нечитаемый файл, требуется повторная подача.", "flag": "Низкое качество данных",
         "temperature": 80.0, "production24h": 35.0, "tubing_internal_p": 140.0,
         "tubing_external_p": 65.0, "annulus_p": 12.0, "pump_strokes": 4,
         "created_at": datetime.utcnow() - timedelta(days=1, hours=11)},
        {"id": "r-6", "well_id": "w-20", "operator_id": "u-op-01", "status": "approved", "ai_score": 94,
         "summary": "Все параметры в пределах нормы.", "temperature": 70.0, "production24h": 48.0,
         "tubing_internal_p": 122.0, "tubing_external_p": 57.0, "annulus_p": 8.0, "pump_strokes": 6,
         "created_at": datetime.utcnow() - timedelta(days=2)},
        {"id": "r-7", "well_id": "w-22", "operator_id": "u-op-01", "status": "pending", "ai_score": 78,
         "summary": "Зафиксировано падение пластового давления.", "temperature": 75.0, "production24h": 32.0,
         "tubing_internal_p": 108.0, "tubing_external_p": 48.0, "annulus_p": 6.0, "pump_strokes": 5,
         "created_at": datetime.utcnow() - timedelta(days=2, hours=3)},
    ]
    for rd in report_seeds:
        r = models.Report(
            id=rd["id"],
            well_id=rd["well_id"],
            operator_id=rd["operator_id"],
            status=rd["status"],
            ai_score=rd["ai_score"],
            summary=rd["summary"],
            flag=rd.get("flag"),
            temperature=rd.get("temperature"),
            production24h=rd.get("production24h"),
            tubing_internal_p=rd.get("tubing_internal_p"),
            tubing_external_p=rd.get("tubing_external_p"),
            annulus_p=rd.get("annulus_p"),
            pump_strokes=rd.get("pump_strokes"),
            created_at=rd.get("created_at", datetime.utcnow()),
        )
        db.add(r)
    db.flush()

    # ── Notifications ─────────────────────────────────────────────────────────
    notif_data = [
        {"id": "n-1", "user_id": "u-op-01", "icon": "alert", "title": "AI: Аномалия на UZ-104",
         "body": "Температура выше нормы на 12%. Требуется проверка.", "tone": "warning", "unread": True,
         "created_at": datetime.utcnow() - timedelta(minutes=5)},
        {"id": "n-2", "user_id": "u-op-01", "icon": "check", "title": "Отчёт одобрен",
         "body": "Отчёт по UZ-108 одобрен менеджером.", "tone": "success", "unread": True,
         "created_at": datetime.utcnow() - timedelta(hours=1)},
        {"id": "n-3", "user_id": "u-mg-01", "icon": "calendar", "title": "Событие в календаре",
         "body": "Плановое совещание 26 мая в 10:00.", "tone": "info", "unread": False,
         "created_at": datetime.utcnow() - timedelta(hours=3)},
        {"id": "n-4", "user_id": "u-op-02", "icon": "edit", "title": "Запрос на доработку",
         "body": "Отчёт UZ-117 отклонён, требуется повтор.", "tone": "destructive", "unread": False,
         "created_at": datetime.utcnow() - timedelta(days=1)},
    ]
    for nd in notif_data:
        n = models.Notification(
            id=nd["id"],
            user_id=nd["user_id"],
            icon=nd["icon"],
            title=nd["title"],
            body=nd["body"],
            tone=nd["tone"],
            unread=nd["unread"],
            created_at=nd["created_at"],
        )
        db.add(n)
    db.flush()

    # ── Calendar Events ───────────────────────────────────────────────────────
    now = datetime.utcnow()
    events_data = [
        {"id": "e-1", "title": "Плановый осмотр UZ-104", "date": now + timedelta(days=1, hours=10), "event_type": "Осмотр"},
        {"id": "e-2", "title": "Совещание менеджеров", "date": now + timedelta(days=2, hours=14), "event_type": "Совещание"},
        {"id": "e-3", "title": "Тренинг по безопасности", "date": now + timedelta(days=4, hours=9), "event_type": "Обучение"},
        {"id": "e-4", "title": "Отчёт за месяц — дедлайн", "date": now + timedelta(days=6, hours=18), "event_type": "Дедлайн"},
    ]
    for ed in events_data:
        e = models.CalendarEvent(id=ed["id"], title=ed["title"], date=ed["date"], event_type=ed["event_type"])
        db.add(e)
    db.flush()

    # ── Audit Log ─────────────────────────────────────────────────────────────
    audit_data = [
        {"id": "a-1", "who": "Дана Ж. (manager)", "action": "Одобрила отчёт", "target": "UZ-108", "created_at": datetime.utcnow() - timedelta(hours=2)},
        {"id": "a-2", "who": "Айбек С. (operator)", "action": "Создал отчёт", "target": "UZ-101", "created_at": datetime.utcnow() - timedelta(hours=3)},
        {"id": "a-3", "who": "Ержан К. (director)", "action": "Изменил статус скважины", "target": "UZ-117 → broken", "created_at": datetime.utcnow() - timedelta(days=1, hours=6)},
        {"id": "a-4", "who": "AI Engine", "action": "Отметил аномалию", "target": "UZ-104", "created_at": datetime.utcnow() - timedelta(days=1, hours=8)},
        {"id": "a-5", "who": "Админ", "action": "Создал пользователя", "target": "operator+02@munai.kz", "created_at": datetime.utcnow() - timedelta(days=3)},
    ]
    for ad in audit_data:
        a = models.AuditLog(id=ad["id"], who=ad["who"], action=ad["action"], target=ad["target"], created_at=ad["created_at"])
        db.add(a)

    db.commit()
