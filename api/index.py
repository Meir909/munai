"""
Vercel serverless handler — stdlib only + PyJWT + bcrypt.
No FastAPI, no SQLAlchemy, no Pydantic. Fits in <50MB unzipped.
"""
import sys
import os
import json
import uuid
import sqlite3
import random
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(__file__))

import jwt
from jwt.exceptions import InvalidTokenError
import bcrypt

# ── Config ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "munai-super-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
DB_PATH = os.getenv("DATABASE_URL", "sqlite:////tmp/munai.db").replace("sqlite:////", "/").replace("sqlite:///", "")

db_dir = os.path.dirname(DB_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

# ── DB helpers ────────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL, role TEXT DEFAULT 'operator',
            position TEXT DEFAULT '', region TEXT DEFAULT '', active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS wells (
            id TEXT PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
            status TEXT DEFAULT 'active', product TEXT DEFAULT 'oil',
            production24h REAL DEFAULT 0, temperature REAL DEFAULT 0,
            tubing_internal_p REAL DEFAULT 0, tubing_external_p REAL DEFAULT 0,
            annulus_p REAL DEFAULT 0, pump_strokes INTEGER DEFAULT 0,
            lat REAL DEFAULT 50.0, lng REAL DEFAULT 55.0,
            operator_id TEXT, manager_id TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY, well_id TEXT NOT NULL, operator_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending', ai_score INTEGER DEFAULT 0,
            summary TEXT DEFAULT '', flag TEXT, temperature REAL,
            production24h REAL, tubing_internal_p REAL, tubing_external_p REAL,
            annulus_p REAL, pump_strokes INTEGER, comment TEXT,
            created_at TEXT DEFAULT (datetime('now')), reviewed_at TEXT, reviewed_by TEXT
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, icon TEXT DEFAULT 'info',
            title TEXT NOT NULL, body TEXT DEFAULT '', tone TEXT DEFAULT 'info',
            unread INTEGER DEFAULT 1, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS calendar_events (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, date TEXT NOT NULL,
            event_type TEXT DEFAULT 'Событие', created_by TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY, who TEXT NOT NULL, action TEXT NOT NULL,
            target TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

def _dt(d): return d.strftime("%Y-%m-%d %H:%M:%S")
def _now(): return _dt(datetime.utcnow())

def seed_db():
    conn = get_conn()
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        conn.close(); return
    pw = bcrypt.hashpw(b"demo", bcrypt.gensalt()).decode()
    now = datetime.utcnow()
    conn.executemany("INSERT INTO users(id,name,email,hashed_password,role,position,region,active) VALUES(?,?,?,?,?,?,?,?)", [
        ("u-op-01","Айбек Сарсенов","operator@munai.kz",pw,"operator","Оператор по добыче нефти","Месторождение Узень-3",1),
        ("u-op-02","Нурлан Темиров","n.temirov@munai.kz",pw,"operator","Оператор по добыче нефти","Месторождение Узень-3",1),
        ("u-mg-01","Дана Жумабекова","manager@munai.kz",pw,"manager","Менеджер участка","Участок Северный",1),
        ("u-dr-01","Ержан Касымов","director@munai.kz",pw,"director","Директор по добыче","Регион Мангистау",1),
        ("u-ad-01","Админ Системы","admin@munai.kz",pw,"admin","Системный администратор","HQ",1),
        ("u-op-03","Алия Жакупова","a.zhakupova@munai.kz",pw,"operator","Оператор","Месторождение Узень-2",0),
    ])
    statuses = ["active","active","active","warning","inactive","broken"]
    rnd = random.Random(42)
    wells = []
    for i in range(24):
        st = statuses[i % len(statuses)]
        product = "gas" if i%5==0 else "condensate" if i%7==0 else "oil"
        wells.append((f"w-{i+1}",f"UZ-{101+i}",f"Скважина №{101+i}",st,product,
            round(rnd.uniform(8,78),1),round(rnd.uniform(38,92),1),round(rnd.uniform(45,180),1),
            round(rnd.uniform(20,90),1),round(rnd.uniform(2,18),1),rnd.randint(4,9),
            round(52.0+(i*0.15)%3.0,4),round(52.0+(i*0.23)%5.0,4),
            "u-op-01" if i%2==0 else "u-op-02","u-mg-01",_dt(now),_dt(now)))
    conn.executemany("INSERT INTO wells(id,code,name,status,product,production24h,temperature,tubing_internal_p,tubing_external_p,annulus_p,pump_strokes,lat,lng,operator_id,manager_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", wells)
    conn.executemany("INSERT INTO reports(id,well_id,operator_id,status,ai_score,summary,flag,temperature,production24h,tubing_internal_p,tubing_external_p,annulus_p,pump_strokes,comment,created_at,reviewed_at,reviewed_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
        ("r-1","w-1","u-op-01","pending",92,"Параметры в норме, добыча стабильна.",None,72.0,45.0,120.0,55.0,8.0,6,None,_dt(now-timedelta(hours=2)),None,None),
        ("r-2","w-4","u-op-01","flagged",41,"Температура выше нормы на 12%.","Аномалия температуры",96.0,38.0,135.0,60.0,10.0,5,None,_dt(now-timedelta(hours=3)),None,None),
        ("r-3","w-8","u-op-02","approved",96,"Замер давления выполнен корректно.",None,68.0,52.0,115.0,50.0,7.0,7,None,_dt(now-timedelta(days=1,hours=5)),None,None),
        ("r-4","w-12","u-op-01","approved",88,"Стандартный суточный замер.",None,74.0,41.0,118.0,53.0,9.0,6,None,_dt(now-timedelta(days=1,hours=7)),None,None),
        ("r-5","w-17","u-op-02","rejected",22,"Нечитаемый файл, требуется повторная подача.","Низкое качество данных",80.0,35.0,140.0,65.0,12.0,4,None,_dt(now-timedelta(days=1,hours=11)),None,None),
        ("r-6","w-20","u-op-01","approved",94,"Все параметры в пределах нормы.",None,70.0,48.0,122.0,57.0,8.0,6,None,_dt(now-timedelta(days=2)),None,None),
        ("r-7","w-22","u-op-01","pending",78,"Зафиксировано падение пластового давления.",None,75.0,32.0,108.0,48.0,6.0,5,None,_dt(now-timedelta(days=2,hours=3)),None,None),
    ])
    conn.executemany("INSERT INTO notifications(id,user_id,icon,title,body,tone,unread,created_at) VALUES(?,?,?,?,?,?,?,?)", [
        ("n-1","u-op-01","alert","AI: Аномалия на UZ-104","Температура выше нормы на 12%. Требуется проверка.","warning",1,_dt(now-timedelta(minutes=5))),
        ("n-2","u-op-01","check","Отчёт одобрен","Отчёт по UZ-108 одобрен менеджером.","success",1,_dt(now-timedelta(hours=1))),
        ("n-3","u-mg-01","calendar","Событие в календаре","Плановое совещание 26 мая в 10:00.","info",0,_dt(now-timedelta(hours=3))),
        ("n-4","u-op-02","edit","Запрос на доработку","Отчёт UZ-117 отклонён, требуется повтор.","destructive",0,_dt(now-timedelta(days=1))),
    ])
    conn.executemany("INSERT INTO calendar_events(id,title,date,event_type,created_by) VALUES(?,?,?,?,?)", [
        ("e-1","Плановый осмотр UZ-104",_dt(now+timedelta(days=1,hours=10)),"Осмотр",None),
        ("e-2","Совещание менеджеров",_dt(now+timedelta(days=2,hours=14)),"Совещание",None),
        ("e-3","Тренинг по безопасности",_dt(now+timedelta(days=4,hours=9)),"Обучение",None),
        ("e-4","Отчёт за месяц — дедлайн",_dt(now+timedelta(days=6,hours=18)),"Дедлайн",None),
    ])
    conn.executemany("INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)", [
        ("a-1","Дана Ж. (manager)","Одобрила отчёт","UZ-108",_dt(now-timedelta(hours=2))),
        ("a-2","Айбек С. (operator)","Создал отчёт","UZ-101",_dt(now-timedelta(hours=3))),
        ("a-3","Ержан К. (director)","Изменил статус скважины","UZ-117 → broken",_dt(now-timedelta(days=1,hours=6))),
        ("a-4","AI Engine","Отметил аномалию","UZ-104",_dt(now-timedelta(days=1,hours=8))),
        ("a-5","Админ","Создал пользователя","operator+02@munai.kz",_dt(now-timedelta(days=3))),
    ])
    conn.commit()
    conn.close()

# ── Auth helpers ──────────────────────────────────────────────────────────────
def make_token(user_id):
    exp = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MIN)
    return jwt.encode({"sub": user_id, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        return None

def get_user_from_request(headers, conn):
    auth = headers.get("authorization") or headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    payload = decode_token(auth[7:])
    if not payload:
        return None
    row = conn.execute("SELECT * FROM users WHERE id=? AND active=1", (payload.get("sub",""),)).fetchone()
    return dict(row) if row else None

def user_out(u):
    return {"id":u["id"],"name":u["name"],"email":u["email"],"role":u["role"],
            "position":u["position"] or "","region":u["region"] or "","active":bool(u["active"])}

# ── Response helpers ──────────────────────────────────────────────────────────
def ok(data, status=200):
    body = json.dumps(data, ensure_ascii=False, default=str)
    return {"statusCode": status, "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}, "body": body}

def err(msg, status=400):
    return ok({"detail": msg}, status)

def parse_body(event):
    try:
        raw = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            import base64; raw = base64.b64decode(raw).decode()
        return json.loads(raw)
    except Exception:
        return {}

def get_headers(event):
    return {k.lower(): v for k, v in (event.get("headers") or {}).items()}

def get_path_params(path, pattern):
    """Extract {id} from path given pattern like /wells/{id}"""
    p_parts = path.strip("/").split("/")
    t_parts = pattern.strip("/").split("/")
    if len(p_parts) != len(t_parts):
        return None
    params = {}
    for pp, tp in zip(p_parts, t_parts):
        if tp.startswith("{") and tp.endswith("}"):
            params[tp[1:-1]] = pp
        elif pp != tp:
            return None
    return params

# ── Route handlers ────────────────────────────────────────────────────────────
def handle_auth_login(event, conn):
    body = parse_body(event)
    email = body.get("email","")
    password = body.get("password","")
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not row:
        return err("Неверный email или пароль", 401)
    try:
        ok_pw = bcrypt.checkpw(password.encode(), row["hashed_password"].encode())
    except Exception:
        ok_pw = False
    if not ok_pw:
        return err("Неверный email или пароль", 401)
    if not row["active"]:
        return err("Аккаунт деактивирован", 403)
    token = make_token(row["id"])
    return ok({"access_token": token, "token_type": "bearer", "user": user_out(dict(row))})

def handle_auth_register(event, conn):
    body = parse_body(event)
    email = body.get("email","")
    if conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
        return err("Email уже используется", 400)
    uid = str(uuid.uuid4())
    pw = bcrypt.hashpw(body.get("password","").encode(), bcrypt.gensalt()).decode()
    conn.execute("INSERT INTO users(id,name,email,hashed_password,role,position,region,active) VALUES(?,?,?,?,?,?,?,1)",
        (uid, body.get("name",""), email, pw, body.get("role","operator"), body.get("position",""), body.get("region","")))
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    token = make_token(uid)
    return ok({"access_token": token, "token_type": "bearer", "user": user_out(dict(row))})

def handle_wells_list(event, conn, user):
    qs = event.get("queryStringParameters") or {}
    q = qs.get("q","")
    status = qs.get("status","all")
    sql = "SELECT * FROM wells WHERE 1=1"
    params = []
    if status != "all":
        sql += " AND status=?"; params.append(status)
    if q:
        sql += " AND (code LIKE ? OR name LIKE ?)"; params += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY code"
    rows = conn.execute(sql, params).fetchall()
    return ok([well_out(dict(r), conn) for r in rows])

def well_out(w, conn):
    op = conn.execute("SELECT name FROM users WHERE id=?", (w.get("operator_id",""),)).fetchone()
    mg = conn.execute("SELECT name FROM users WHERE id=?", (w.get("manager_id",""),)).fetchone()
    lr = conn.execute("SELECT created_at FROM reports WHERE well_id=? ORDER BY created_at DESC LIMIT 1", (w["id"],)).fetchone()
    last_report = None
    if lr:
        try:
            ts = datetime.strptime(lr["created_at"], "%Y-%m-%d %H:%M:%S")
            hours = int((datetime.utcnow()-ts).total_seconds()//3600)
            last_report = "Менее часа назад" if hours<1 else f"{hours}ч назад" if hours<24 else f"{hours//24}д назад"
        except Exception: pass
    return {**w, "operator_name": op["name"] if op else None, "manager_name": mg["name"] if mg else None, "last_report": last_report}

def handle_wells_create(event, conn, user):
    if user["role"] not in ("manager","director","admin"):
        return err("Недостаточно прав", 403)
    body = parse_body(event)
    code = body.get("code","")
    if conn.execute("SELECT id FROM wells WHERE code=?", (code,)).fetchone():
        return err("Скважина с таким кодом уже существует", 400)
    wid = str(uuid.uuid4()); now = _now()
    conn.execute("INSERT INTO wells(id,code,name,status,product,production24h,temperature,tubing_internal_p,tubing_external_p,annulus_p,pump_strokes,lat,lng,operator_id,manager_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (wid,code,body.get("name",""),body.get("status","active"),body.get("product","oil"),
         body.get("production24h",0),body.get("temperature",0),body.get("tubing_internal_p",0),
         body.get("tubing_external_p",0),body.get("annulus_p",0),body.get("pump_strokes",0),
         body.get("lat",50.0),body.get("lng",55.0),body.get("operator_id"),body.get("manager_id"),now,now))
    conn.execute("INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()),f"{user['name']} ({user['role']})","Создал скважину",code,now))
    conn.commit()
    row = conn.execute("SELECT * FROM wells WHERE id=?", (wid,)).fetchone()
    return ok(well_out(dict(row), conn))

def handle_wells_update(event, conn, user, well_id):
    if user["role"] not in ("manager","director","admin"):
        return err("Недостаточно прав", 403)
    row = conn.execute("SELECT * FROM wells WHERE id=?", (well_id,)).fetchone()
    if not row: return err("Скважина не найдена", 404)
    body = parse_body(event)
    allowed = ["name","status","product","production24h","temperature","tubing_internal_p",
               "tubing_external_p","annulus_p","pump_strokes","lat","lng","operator_id","manager_id"]
    updates = {k: v for k, v in body.items() if k in allowed and v is not None}
    now = _now(); updates["updated_at"] = now
    set_clause = ", ".join(f"{k}=?" for k in updates)
    conn.execute(f"UPDATE wells SET {set_clause} WHERE id=?", list(updates.values())+[well_id])
    conn.execute("INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()),f"{user['name']} ({user['role']})","Обновил скважину",row["code"],now))
    conn.commit()
    row = conn.execute("SELECT * FROM wells WHERE id=?", (well_id,)).fetchone()
    return ok(well_out(dict(row), conn))

def handle_wells_delete(event, conn, user, well_id):
    if user["role"] not in ("director","admin"):
        return err("Недостаточно прав", 403)
    row = conn.execute("SELECT code FROM wells WHERE id=?", (well_id,)).fetchone()
    if not row: return err("Скважина не найдена", 404)
    conn.execute("INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()),f"{user['name']} ({user['role']})","Удалил скважину",row["code"],_now()))
    conn.execute("DELETE FROM wells WHERE id=?", (well_id,))
    conn.commit()
    return ok({"ok": True})

def report_out(r, conn):
    well = conn.execute("SELECT code,name FROM wells WHERE id=?", (r.get("well_id",""),)).fetchone()
    op = conn.execute("SELECT name FROM users WHERE id=?", (r.get("operator_id",""),)).fetchone()
    return {**r, "well_code": well["code"] if well else None, "well_name": well["name"] if well else None,
            "operator_name": op["name"] if op else None}

def ai_score(body):
    score = 100; flag = None; issues = []
    temp = body.get("temperature")
    if temp and temp > 90: score -= 30; issues.append("Критически высокая температура"); flag = "Аномалия температуры"
    elif temp and temp > 80: score -= 15; issues.append("Повышенная температура")
    prod = body.get("production24h")
    if prod and prod < 10: score -= 20; issues.append("Низкая суточная добыча")
    tip = body.get("tubing_internal_p")
    if tip and tip > 160: score -= 25; issues.append("Высокое давление в НКТ"); flag = flag or "Превышение давления"
    ps = body.get("pump_strokes")
    if ps and ps < 3: score -= 20; issues.append("Низкая частота качания")
    summary = "Параметры в норме." if not issues else "Выявлено: " + "; ".join(issues) + "."
    return max(0, score), summary, flag

def handle_reports_list(event, conn, user):
    qs = event.get("queryStringParameters") or {}
    q = qs.get("q",""); status = qs.get("status","all")
    sql = "SELECT * FROM reports WHERE 1=1"; params = []
    if user["role"] == "operator":
        sql += " AND operator_id=?"; params.append(user["id"])
    if status != "all":
        sql += " AND status=?"; params.append(status)
    if q:
        sql += " AND (id LIKE ? OR well_id LIKE ?)"; params += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    return ok([report_out(dict(r), conn) for r in rows])

def handle_reports_pending(event, conn, user):
    if user["role"] not in ("manager","director","admin"): return err("Недостаточно прав", 403)
    rows = conn.execute("SELECT * FROM reports WHERE status='pending' ORDER BY created_at DESC").fetchall()
    return ok([report_out(dict(r), conn) for r in rows])

def handle_reports_create(event, conn, user):
    body = parse_body(event)
    well_id = body.get("well_id","")
    if not conn.execute("SELECT id FROM wells WHERE id=?", (well_id,)).fetchone():
        return err("Скважина не найдена", 404)
    score, summary, flag = ai_score(body)
    rid = str(uuid.uuid4()); now = _now()
    status = "flagged" if flag else "pending"
    conn.execute("INSERT INTO reports(id,well_id,operator_id,status,ai_score,summary,flag,temperature,production24h,tubing_internal_p,tubing_external_p,annulus_p,pump_strokes,comment,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (rid,well_id,user["id"],status,score,summary,flag,body.get("temperature"),body.get("production24h"),
         body.get("tubing_internal_p"),body.get("tubing_external_p"),body.get("annulus_p"),body.get("pump_strokes"),body.get("comment"),now))
    if flag:
        conn.execute("INSERT INTO notifications(id,user_id,icon,title,body,tone,unread,created_at) VALUES(?,?,?,?,?,?,1,?)",
            (str(uuid.uuid4()),user["id"],"alert","AI: Аномалия обнаружена",flag,"warning",now))
    conn.execute("INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()),f"{user['name']} ({user['role']})","Создал отчёт",well_id,now))
    conn.commit()
    row = conn.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
    return ok(report_out(dict(row), conn))

def handle_reports_review(event, conn, user, report_id):
    if user["role"] not in ("manager","director","admin"): return err("Недостаточно прав", 403)
    row = conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    if not row: return err("Отчёт не найден", 404)
    body = parse_body(event)
    new_status = body.get("status","")
    if new_status not in ("approved","rejected"): return err("Неверный статус", 400)
    now = _now()
    conn.execute("UPDATE reports SET status=?,reviewed_at=?,reviewed_by=? WHERE id=?", (new_status,now,user["id"],report_id))
    title = "Отчёт одобрен" if new_status=="approved" else "Отчёт отклонён"
    tone = "success" if new_status=="approved" else "destructive"
    conn.execute("INSERT INTO notifications(id,user_id,icon,title,body,tone,unread,created_at) VALUES(?,?,?,?,?,?,1,?)",
        (str(uuid.uuid4()),row["operator_id"],"check" if new_status=="approved" else "x",title,body.get("comment",""),tone,now))
    conn.execute("INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()),f"{user['name']} ({user['role']})",f"{'Одобрил' if new_status=='approved' else 'Отклонил'} отчёт",report_id,now))
    conn.commit()
    row = conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    return ok(report_out(dict(row), conn))

def handle_reports_delete(event, conn, user, report_id):
    row = conn.execute("SELECT operator_id FROM reports WHERE id=?", (report_id,)).fetchone()
    if not row: return err("Отчёт не найден", 404)
    if user["role"] not in ("manager","director","admin") and row["operator_id"] != user["id"]:
        return err("Недостаточно прав", 403)
    conn.execute("DELETE FROM reports WHERE id=?", (report_id,)); conn.commit()
    return ok({"ok": True})

def handle_users_list(event, conn, user):
    if user["role"] not in ("manager","director","admin"): return err("Недостаточно прав", 403)
    rows = conn.execute("SELECT * FROM users ORDER BY name").fetchall()
    return ok([user_out(dict(r)) for r in rows])

def handle_users_create(event, conn, user):
    if user["role"] != "admin": return err("Только администратор", 403)
    body = parse_body(event)
    if conn.execute("SELECT id FROM users WHERE email=?", (body.get("email",""),)).fetchone():
        return err("Email уже используется", 400)
    uid = str(uuid.uuid4())
    pw = bcrypt.hashpw(body.get("password","").encode(), bcrypt.gensalt()).decode()
    conn.execute("INSERT INTO users(id,name,email,hashed_password,role,position,region,active) VALUES(?,?,?,?,?,?,?,1)",
        (uid,body.get("name",""),body.get("email",""),pw,body.get("role","operator"),body.get("position",""),body.get("region","")))
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return ok(user_out(dict(row)))

def handle_users_update(event, conn, user, user_id):
    if user["role"] != "admin" and user["id"] != user_id: return err("Недостаточно прав", 403)
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not row: return err("Пользователь не найден", 404)
    body = parse_body(event)
    allowed = ["name","role","position","region","active"]
    updates = {k: v for k, v in body.items() if k in allowed and v is not None}
    if "password" in body and body["password"]:
        updates["hashed_password"] = bcrypt.hashpw(body["password"].encode(), bcrypt.gensalt()).decode()
    if "active" in updates: updates["active"] = 1 if updates["active"] else 0
    if updates:
        set_clause = ", ".join(f"{k}=?" for k in updates)
        conn.execute(f"UPDATE users SET {set_clause} WHERE id=?", list(updates.values())+[user_id])
        conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return ok(user_out(dict(row)))

def handle_users_delete(event, conn, user, user_id):
    if user["role"] != "admin": return err("Только администратор", 403)
    if not conn.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone():
        return err("Пользователь не найден", 404)
    conn.execute("DELETE FROM users WHERE id=?", (user_id,)); conn.commit()
    return ok({"ok": True})

def handle_notifications_list(event, conn, user):
    rows = conn.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC", (user["id"],)).fetchall()
    return ok([{"id":r["id"],"icon":r["icon"],"title":r["title"],"body":r["body"],"tone":r["tone"],"unread":bool(r["unread"]),"created_at":r["created_at"]} for r in rows])

def handle_notifications_read(event, conn, user, notif_id):
    conn.execute("UPDATE notifications SET unread=0 WHERE id=? AND user_id=?", (notif_id, user["id"])); conn.commit()
    return ok({"ok": True})

def handle_notifications_read_all(event, conn, user):
    conn.execute("UPDATE notifications SET unread=0 WHERE user_id=?", (user["id"],)); conn.commit()
    return ok({"ok": True})

def handle_calendar_list(event, conn, user):
    rows = conn.execute("SELECT * FROM calendar_events ORDER BY date").fetchall()
    return ok([{"id":r["id"],"title":r["title"],"date":r["date"],"event_type":r["event_type"],"created_by":r["created_by"]} for r in rows])

def handle_calendar_create(event, conn, user):
    body = parse_body(event)
    eid = str(uuid.uuid4()); now = _now()
    conn.execute("INSERT INTO calendar_events(id,title,date,event_type,created_by,created_at) VALUES(?,?,?,?,?,?)",
        (eid,body.get("title",""),body.get("date",now),body.get("event_type","Событие"),user["id"],now))
    conn.commit()
    row = conn.execute("SELECT * FROM calendar_events WHERE id=?", (eid,)).fetchone()
    return ok({"id":row["id"],"title":row["title"],"date":row["date"],"event_type":row["event_type"],"created_by":row["created_by"]})

def handle_calendar_delete(event, conn, user, event_id):
    conn.execute("DELETE FROM calendar_events WHERE id=?", (event_id,)); conn.commit()
    return ok({"ok": True})

def handle_dashboard_stats(event, conn, user):
    active_wells = conn.execute("SELECT COUNT(*) FROM wells WHERE status='active'").fetchone()[0]
    warning_wells = conn.execute("SELECT COUNT(*) FROM wells WHERE status='warning'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM reports WHERE status='pending'").fetchone()[0]
    flagged = conn.execute("SELECT COUNT(*) FROM reports WHERE status='flagged'").fetchone()[0]
    total_prod = conn.execute("SELECT COALESCE(SUM(production24h),0) FROM wells WHERE status='active'").fetchone()[0]
    now = datetime.utcnow()
    trend = [{"day":(now-timedelta(days=i)).strftime("%d.%m"),"oil":round(total_prod*(0.85+(i%3)*0.05),1),"gas":round(total_prod*0.1*(0.9+(i%4)*0.03),1)} for i in range(6,-1,-1)]
    statuses = conn.execute("SELECT status, COUNT(*) as cnt FROM wells GROUP BY status").fetchall()
    return ok({"active_wells":active_wells,"warning_wells":warning_wells,"pending_reports":pending,
               "flagged_reports":flagged,"total_production":round(total_prod,1),"production_trend":trend,
               "well_statuses":[{"status":r["status"],"count":r["cnt"]} for r in statuses]})

def handle_audit_list(event, conn, user):
    if user["role"] not in ("manager","director","admin"): return err("Недостаточно прав", 403)
    rows = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100").fetchall()
    return ok([{"id":r["id"],"who":r["who"],"action":r["action"],"target":r["target"],"created_at":r["created_at"]} for r in rows])

def handle_ai_chat(event, conn, user):
    body = parse_body(event)
    msg = body.get("message","").lower()
    n = conn.execute("SELECT COUNT(*) FROM wells").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM wells WHERE status='active'").fetchone()[0]
    warning = conn.execute("SELECT COUNT(*) FROM wells WHERE status='warning'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM reports WHERE status='pending'").fetchone()[0]
    flagged = conn.execute("SELECT COUNT(*) FROM reports WHERE status='flagged'").fetchone()[0]
    prod = conn.execute("SELECT COALESCE(SUM(production24h),0) FROM wells WHERE status='active'").fetchone()[0]
    if any(k in msg for k in ("скважин","well")):
        reply = f"На платформе {n} скважин. {active} активных, {warning} требуют внимания."
        sugg = ["Показать карту скважин","Отчёты по скважинам"]
    elif any(k in msg for k in ("добыч","production")):
        reply = f"Суммарная суточная добыча составляет {prod:.0f} т/сут."
        sugg = ["Показать KPI дашборд","Детализация по скважинам"]
    elif any(k in msg for k in ("отчёт","report")):
        reply = f"Ожидают проверки {pending} отчётов. {flagged} помечены AI как аномальные."
        sugg = ["Перейти к согласованиям","Создать новый отчёт"]
    elif any(k in msg for k in ("аномал","anomal")):
        reply = f"AI выявил {flagged} аномалий. Рекомендую срочно проверить скважины."
        sugg = ["Согласования","Карта скважин"]
    elif any(k in msg for k in ("привет","hello","здравствуй")):
        reply = "Привет! Я AI-ассистент MUNAI. Спросите о скважинах, добыче, отчётах или аномалиях."
        sugg = ["Статистика добычи","Статус скважин","Ожидающие отчёты"]
    else:
        reply = "Я обрабатываю данные платформы MUNAI. Спросите о скважинах, добыче, отчётах или аномалиях."
        sugg = ["Статистика добычи","Статус скважин"]
    return ok({"reply": reply, "suggestions": sugg})

def handle_ai_insights(event, conn, user):
    warning = conn.execute("SELECT COUNT(*) FROM wells WHERE status='warning'").fetchone()[0]
    flagged = conn.execute("SELECT COUNT(*) FROM reports WHERE status='flagged'").fetchone()[0]
    return ok({"insights":[{"type":"warning","message":f"{warning} скважин требуют внимания"},{"type":"info","message":f"{flagged} отчётов помечены AI"}]})

# ── Cold-start init ───────────────────────────────────────────────────────────
init_db()
seed_db()

# ── Router ────────────────────────────────────────────────────────────────────
def route(event, context):
    method = event.get("httpMethod", "GET").upper()
    raw_path = event.get("path", "/")
    # Strip /api prefix
    path = raw_path[4:] if raw_path.startswith("/api") else raw_path

    headers = get_headers(event)

    # CORS preflight
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"*"}, "body": ""}

    # Health
    if path in ("/", "/health"):
        return ok({"status": "ok", "service": "MUNAI API", "version": "1.0.0"})

    conn = get_conn()
    try:
        # Public routes
        if path == "/auth/login" and method == "POST":
            return handle_auth_login(event, conn)
        if path == "/auth/register" and method == "POST":
            return handle_auth_register(event, conn)

        # Auth required
        user = get_user_from_request(headers, conn)
        if not user:
            return err("Not authenticated", 401)

        # Auth me
        if path == "/auth/me" and method == "GET":
            return ok(user_out(user))

        # Wells
        if path == "/wells" and method == "GET":
            return handle_wells_list(event, conn, user)
        if path == "/wells" and method == "POST":
            return handle_wells_create(event, conn, user)
        p = get_path_params(path, "/wells/{id}")
        if p:
            if method == "GET":
                row = conn.execute("SELECT * FROM wells WHERE id=?", (p["id"],)).fetchone()
                return ok(well_out(dict(row), conn)) if row else err("Не найдена", 404)
            if method == "PUT": return handle_wells_update(event, conn, user, p["id"])
            if method == "DELETE": return handle_wells_delete(event, conn, user, p["id"])

        # Reports
        if path == "/reports" and method == "GET": return handle_reports_list(event, conn, user)
        if path == "/reports" and method == "POST": return handle_reports_create(event, conn, user)
        if path == "/reports/pending" and method == "GET": return handle_reports_pending(event, conn, user)
        p = get_path_params(path, "/reports/{id}")
        if p:
            if method == "GET":
                row = conn.execute("SELECT * FROM reports WHERE id=?", (p["id"],)).fetchone()
                return ok(report_out(dict(row), conn)) if row else err("Не найден", 404)
            if method == "DELETE": return handle_reports_delete(event, conn, user, p["id"])
        p = get_path_params(path, "/reports/{id}/review")
        if p and method == "POST": return handle_reports_review(event, conn, user, p["id"])

        # Users
        if path == "/users" and method == "GET": return handle_users_list(event, conn, user)
        if path == "/users" and method == "POST": return handle_users_create(event, conn, user)
        p = get_path_params(path, "/users/{id}")
        if p:
            if method == "PUT": return handle_users_update(event, conn, user, p["id"])
            if method == "DELETE": return handle_users_delete(event, conn, user, p["id"])

        # Notifications
        if path == "/notifications" and method == "GET": return handle_notifications_list(event, conn, user)
        if path == "/notifications/read-all" and method == "POST": return handle_notifications_read_all(event, conn, user)
        p = get_path_params(path, "/notifications/{id}/read")
        if p and method == "POST": return handle_notifications_read(event, conn, user, p["id"])

        # Calendar
        if path == "/calendar" and method == "GET": return handle_calendar_list(event, conn, user)
        if path == "/calendar" and method == "POST": return handle_calendar_create(event, conn, user)
        p = get_path_params(path, "/calendar/{id}")
        if p and method == "DELETE": return handle_calendar_delete(event, conn, user, p["id"])

        # Dashboard
        if path == "/dashboard/stats" and method == "GET": return handle_dashboard_stats(event, conn, user)

        # Audit
        if path == "/audit" and method == "GET": return handle_audit_list(event, conn, user)

        # AI
        if path == "/ai/chat" and method == "POST": return handle_ai_chat(event, conn, user)
        if path == "/ai/insights" and method == "GET": return handle_ai_insights(event, conn, user)

        return err("Not found", 404)
    except Exception as e:
        import traceback; traceback.print_exc()
        return err(f"Internal error: {str(e)}", 500)
    finally:
        conn.close()


def handler(event, context):
    return route(event, context)
