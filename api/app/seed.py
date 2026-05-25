"""Seed the SQLite database with demo data."""
import random
from datetime import datetime, timedelta
from app.auth import hash_password


def _dt(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")


def seed_db(conn):
    row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    if row[0] > 0:
        return

    pw = hash_password("demo")
    now = datetime.utcnow()

    users = [
        ("u-op-01", "Айбек Сарсенов", "operator@munai.kz", pw, "operator", "Оператор по добыче нефти", "Месторождение Узень-3", 1),
        ("u-op-02", "Нурлан Темиров", "n.temirov@munai.kz", pw, "operator", "Оператор по добыче нефти", "Месторождение Узень-3", 1),
        ("u-mg-01", "Дана Жумабекова", "manager@munai.kz", pw, "manager", "Менеджер участка", "Участок Северный", 1),
        ("u-dr-01", "Ержан Касымов", "director@munai.kz", pw, "director", "Директор по добыче", "Регион Мангистау", 1),
        ("u-ad-01", "Админ Системы", "admin@munai.kz", pw, "admin", "Системный администратор", "HQ", 1),
        ("u-op-03", "Алия Жакупова", "a.zhakupova@munai.kz", pw, "operator", "Оператор по добыче нефти", "Месторождение Узень-2", 0),
    ]
    conn.executemany(
        "INSERT INTO users(id,name,email,hashed_password,role,position,region,active) VALUES(?,?,?,?,?,?,?,?)",
        users
    )

    statuses = ["active", "active", "active", "warning", "inactive", "broken"]
    rnd = random.Random(42)
    wells = []
    for i in range(24):
        st = statuses[i % len(statuses)]
        product = "gas" if i % 5 == 0 else "condensate" if i % 7 == 0 else "oil"
        wells.append((
            f"w-{i+1}", f"UZ-{101+i}", f"Скважина №{101+i}", st, product,
            round(rnd.uniform(8, 78), 1), round(rnd.uniform(38, 92), 1),
            round(rnd.uniform(45, 180), 1), round(rnd.uniform(20, 90), 1),
            round(rnd.uniform(2, 18), 1), rnd.randint(4, 9),
            round(52.0 + (i * 0.15) % 3.0, 4), round(52.0 + (i * 0.23) % 5.0, 4),
            "u-op-01" if i % 2 == 0 else "u-op-02", "u-mg-01",
            _dt(now), _dt(now)
        ))
    conn.executemany(
        "INSERT INTO wells(id,code,name,status,product,production24h,temperature,"
        "tubing_internal_p,tubing_external_p,annulus_p,pump_strokes,lat,lng,"
        "operator_id,manager_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        wells
    )

    reports = [
        ("r-1","w-1","u-op-01","pending",92,"Параметры в норме, добыча стабильна.",None,72.0,45.0,120.0,55.0,8.0,6,None,_dt(now-timedelta(hours=2)),None,None),
        ("r-2","w-4","u-op-01","flagged",41,"Температура выше нормы на 12%.","Аномалия температуры",96.0,38.0,135.0,60.0,10.0,5,None,_dt(now-timedelta(hours=3)),None,None),
        ("r-3","w-8","u-op-02","approved",96,"Замер давления выполнен корректно.",None,68.0,52.0,115.0,50.0,7.0,7,None,_dt(now-timedelta(days=1,hours=5)),None,None),
        ("r-4","w-12","u-op-01","approved",88,"Стандартный суточный замер.",None,74.0,41.0,118.0,53.0,9.0,6,None,_dt(now-timedelta(days=1,hours=7)),None,None),
        ("r-5","w-17","u-op-02","rejected",22,"Нечитаемый файл, требуется повторная подача.","Низкое качество данных",80.0,35.0,140.0,65.0,12.0,4,None,_dt(now-timedelta(days=1,hours=11)),None,None),
        ("r-6","w-20","u-op-01","approved",94,"Все параметры в пределах нормы.",None,70.0,48.0,122.0,57.0,8.0,6,None,_dt(now-timedelta(days=2)),None,None),
        ("r-7","w-22","u-op-01","pending",78,"Зафиксировано падение пластового давления.",None,75.0,32.0,108.0,48.0,6.0,5,None,_dt(now-timedelta(days=2,hours=3)),None,None),
    ]
    conn.executemany(
        "INSERT INTO reports(id,well_id,operator_id,status,ai_score,summary,flag,"
        "temperature,production24h,tubing_internal_p,tubing_external_p,annulus_p,"
        "pump_strokes,comment,created_at,reviewed_at,reviewed_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        reports
    )

    notifs = [
        ("n-1","u-op-01","alert","AI: Аномалия на UZ-104","Температура выше нормы на 12%. Требуется проверка.","warning",1,_dt(now-timedelta(minutes=5))),
        ("n-2","u-op-01","check","Отчёт одобрен","Отчёт по UZ-108 одобрен менеджером.","success",1,_dt(now-timedelta(hours=1))),
        ("n-3","u-mg-01","calendar","Событие в календаре","Плановое совещание 26 мая в 10:00.","info",0,_dt(now-timedelta(hours=3))),
        ("n-4","u-op-02","edit","Запрос на доработку","Отчёт UZ-117 отклонён, требуется повтор.","destructive",0,_dt(now-timedelta(days=1))),
    ]
    conn.executemany(
        "INSERT INTO notifications(id,user_id,icon,title,body,tone,unread,created_at) VALUES(?,?,?,?,?,?,?,?)",
        notifs
    )

    events = [
        ("e-1","Плановый осмотр UZ-104",_dt(now+timedelta(days=1,hours=10)),"Осмотр",None),
        ("e-2","Совещание менеджеров",_dt(now+timedelta(days=2,hours=14)),"Совещание",None),
        ("e-3","Тренинг по безопасности",_dt(now+timedelta(days=4,hours=9)),"Обучение",None),
        ("e-4","Отчёт за месяц — дедлайн",_dt(now+timedelta(days=6,hours=18)),"Дедлайн",None),
    ]
    conn.executemany(
        "INSERT INTO calendar_events(id,title,date,event_type,created_by) VALUES(?,?,?,?,?)",
        events
    )

    audits = [
        ("a-1","Дана Ж. (manager)","Одобрила отчёт","UZ-108",_dt(now-timedelta(hours=2))),
        ("a-2","Айбек С. (operator)","Создал отчёт","UZ-101",_dt(now-timedelta(hours=3))),
        ("a-3","Ержан К. (director)","Изменил статус скважины","UZ-117 → broken",_dt(now-timedelta(days=1,hours=6))),
        ("a-4","AI Engine","Отметил аномалию","UZ-104",_dt(now-timedelta(days=1,hours=8))),
        ("a-5","Админ","Создал пользователя","operator+02@munai.kz",_dt(now-timedelta(days=3))),
    ]
    conn.executemany(
        "INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
        audits
    )

    conn.commit()
