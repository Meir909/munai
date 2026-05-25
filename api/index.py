"""Vercel serverless entry — FastAPI + Mangum, sqlite3 вместо SQLAlchemy."""
import sys
import os
import uuid
import sqlite3
import random
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Any

sys.path.insert(0, os.path.dirname(__file__))

import jwt
from jwt.exceptions import InvalidTokenError
import bcrypt
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from mangum import Mangum

# ── Config ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "munai-super-secret-key-2026")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
DB_PATH = os.getenv("DATABASE_URL", "sqlite:////tmp/munai.db").replace("sqlite:////", "/").replace("sqlite:///", "")

db_dir = os.path.dirname(DB_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

# ── DB ────────────────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
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
            created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY, well_id TEXT NOT NULL, operator_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending', ai_score INTEGER DEFAULT 0,
            summary TEXT DEFAULT '', flag TEXT,
            temperature REAL, production24h REAL, tubing_internal_p REAL,
            tubing_external_p REAL, annulus_p REAL, pump_strokes INTEGER, comment TEXT,
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
    rnd = random.Random(42)
    statuses = ["active","active","active","warning","inactive","broken"]
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
        ("n-1","u-op-01","alert","AI: Аномалия на UZ-104","Температура выше нормы на 12%","warning",1,_dt(now-timedelta(minutes=5))),
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

# ── Auth ──────────────────────────────────────────────────────────────────────
bearer = HTTPBearer(auto_error=False)

def make_token(uid: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MIN)
    return jwt.encode({"sub": uid, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()

def current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
                 db: sqlite3.Connection = Depends(get_db)):
    if not creds:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    uid = payload.get("sub")
    row = db.execute("SELECT * FROM users WHERE id=? AND active=1", (uid,)).fetchone()
    if not row:
        raise HTTPException(401, "User not found")
    return dict(row)

def u_out(r):
    return {"id":r["id"],"name":r["name"],"email":r["email"],"role":r["role"],
            "position":r["position"] or "","region":r["region"] or "","active":bool(r["active"])}

def now_str(): return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# ── Schemas (Pydantic v1) ─────────────────────────────────────────────────────
class LoginReq(BaseModel):
    email: str; password: str

class RegisterReq(BaseModel):
    name: str; email: str; password: str
    role: str = "operator"; position: str = ""; region: str = ""

class WellCreate(BaseModel):
    code: str; name: str; status: str = "active"; product: str = "oil"
    production24h: float = 0; temperature: float = 0
    tubing_internal_p: float = 0; tubing_external_p: float = 0
    annulus_p: float = 0; pump_strokes: int = 0
    lat: float = 50.0; lng: float = 55.0
    operator_id: Optional[str] = None; manager_id: Optional[str] = None

class WellUpdate(BaseModel):
    name: Optional[str] = None; status: Optional[str] = None; product: Optional[str] = None
    production24h: Optional[float] = None; temperature: Optional[float] = None
    tubing_internal_p: Optional[float] = None; tubing_external_p: Optional[float] = None
    annulus_p: Optional[float] = None; pump_strokes: Optional[int] = None
    lat: Optional[float] = None; lng: Optional[float] = None
    operator_id: Optional[str] = None; manager_id: Optional[str] = None

class ReportCreate(BaseModel):
    well_id: str; temperature: Optional[float] = None; production24h: Optional[float] = None
    tubing_internal_p: Optional[float] = None; tubing_external_p: Optional[float] = None
    annulus_p: Optional[float] = None; pump_strokes: Optional[int] = None
    comment: Optional[str] = None

class ReportReview(BaseModel):
    status: str; comment: Optional[str] = None

class UserCreate(BaseModel):
    name: str; email: str; password: str
    role: str = "operator"; position: str = ""; region: str = ""

class UserUpdate(BaseModel):
    name: Optional[str] = None; role: Optional[str] = None
    position: Optional[str] = None; region: Optional[str] = None
    active: Optional[bool] = None; password: Optional[str] = None

class CalEventCreate(BaseModel):
    title: str; date: str; event_type: str = "Событие"

class AIChatReq(BaseModel):
    message: str

# ── App ───────────────────────────────────────────────────────────────────────
init_db()
seed_db()

app = FastAPI(title="MUNAI API", version="1.0.0", root_path="/api")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ── Helpers ───────────────────────────────────────────────────────────────────
def well_row(r, db):
    r = dict(r)
    op = db.execute("SELECT name FROM users WHERE id=?", (r.get("operator_id") or "",)).fetchone()
    mg = db.execute("SELECT name FROM users WHERE id=?", (r.get("manager_id") or "",)).fetchone()
    lr = db.execute("SELECT created_at FROM reports WHERE well_id=? ORDER BY created_at DESC LIMIT 1", (r["id"],)).fetchone()
    last = None
    if lr:
        try:
            ts = datetime.strptime(lr["created_at"], "%Y-%m-%d %H:%M:%S")
            h = int((datetime.utcnow()-ts).total_seconds()//3600)
            last = "Менее часа назад" if h<1 else f"{h}ч назад" if h<24 else f"{h//24}д назад"
        except: pass
    r["operator_name"] = op["name"] if op else None
    r["manager_name"] = mg["name"] if mg else None
    r["last_report"] = last
    return r

def report_row(r, db):
    r = dict(r)
    w = db.execute("SELECT code,name FROM wells WHERE id=?", (r.get("well_id") or "",)).fetchone()
    op = db.execute("SELECT name FROM users WHERE id=?", (r.get("operator_id") or "",)).fetchone()
    r["well_code"] = w["code"] if w else None
    r["well_name"] = w["name"] if w else None
    r["operator_name"] = op["name"] if op else None
    return r

def ai_score(b: ReportCreate):
    score = 100; flag = None; issues = []
    if b.temperature and b.temperature > 90: score -= 30; flag = "Аномалия температуры"; issues.append("Критически высокая температура")
    elif b.temperature and b.temperature > 80: score -= 15; issues.append("Повышенная температура")
    if b.production24h and b.production24h < 10: score -= 20; issues.append("Низкая суточная добыча")
    if b.tubing_internal_p and b.tubing_internal_p > 160: score -= 25; flag = flag or "Превышение давления"; issues.append("Высокое давление")
    if b.pump_strokes and b.pump_strokes < 3: score -= 20; issues.append("Низкая частота качания")
    summary = "Параметры в норме." if not issues else "Выявлено: " + "; ".join(issues) + "."
    return max(0, score), summary, flag

# ── Routes: Auth ──────────────────────────────────────────────────────────────
@app.get("/"); def root(): return {"status": "ok", "service": "MUNAI API"}
@app.get("/health"); def health(): return {"status": "healthy"}

@app.post("/auth/login")
def login(b: LoginReq, db=Depends(get_db)):
    r = db.execute("SELECT * FROM users WHERE email=?", (b.email,)).fetchone()
    if not r: raise HTTPException(401, "Неверный email или пароль")
    try: ok_pw = bcrypt.checkpw(b.password.encode(), r["hashed_password"].encode())
    except: ok_pw = False
    if not ok_pw: raise HTTPException(401, "Неверный email или пароль")
    if not r["active"]: raise HTTPException(403, "Аккаунт деактивирован")
    return {"access_token": make_token(r["id"]), "token_type": "bearer", "user": u_out(dict(r))}

@app.post("/auth/register")
def register(b: RegisterReq, db=Depends(get_db)):
    if db.execute("SELECT id FROM users WHERE email=?", (b.email,)).fetchone():
        raise HTTPException(400, "Email уже используется")
    uid = str(uuid.uuid4())
    pw = bcrypt.hashpw(b.password.encode(), bcrypt.gensalt()).decode()
    db.execute("INSERT INTO users(id,name,email,hashed_password,role,position,region,active) VALUES(?,?,?,?,?,?,?,1)",
               (uid, b.name, b.email, pw, b.role, b.position, b.region))
    r = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return {"access_token": make_token(uid), "token_type": "bearer", "user": u_out(dict(r))}

@app.get("/auth/me")
def me(u=Depends(current_user)): return u_out(u)

# ── Routes: Wells ─────────────────────────────────────────────────────────────
@app.get("/wells")
def wells_list(q: str = "", status: str = "all", db=Depends(get_db), u=Depends(current_user)):
    sql = "SELECT * FROM wells WHERE 1=1"; params = []
    if status != "all": sql += " AND status=?"; params.append(status)
    if q: sql += " AND (code LIKE ? OR name LIKE ?)"; params += [f"%{q}%", f"%{q}%"]
    return [well_row(r, db) for r in db.execute(sql+" ORDER BY code", params).fetchall()]

@app.post("/wells")
def wells_create(b: WellCreate, db=Depends(get_db), u=Depends(current_user)):
    if u["role"] not in ("manager","director","admin"): raise HTTPException(403, "Недостаточно прав")
    if db.execute("SELECT id FROM wells WHERE code=?", (b.code,)).fetchone():
        raise HTTPException(400, "Скважина с таким кодом уже существует")
    wid = str(uuid.uuid4()); n = now_str()
    db.execute("INSERT INTO wells(id,code,name,status,product,production24h,temperature,tubing_internal_p,tubing_external_p,annulus_p,pump_strokes,lat,lng,operator_id,manager_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (wid,b.code,b.name,b.status,b.product,b.production24h,b.temperature,b.tubing_internal_p,b.tubing_external_p,b.annulus_p,b.pump_strokes,b.lat,b.lng,b.operator_id,b.manager_id,n,n))
    db.execute("INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
               (str(uuid.uuid4()),f"{u['name']} ({u['role']})","Создал скважину",b.code,n))
    return well_row(db.execute("SELECT * FROM wells WHERE id=?", (wid,)).fetchone(), db)

@app.get("/wells/{well_id}")
def wells_get(well_id: str, db=Depends(get_db), u=Depends(current_user)):
    r = db.execute("SELECT * FROM wells WHERE id=?", (well_id,)).fetchone()
    if not r: raise HTTPException(404, "Скважина не найдена")
    return well_row(r, db)

@app.put("/wells/{well_id}")
def wells_update(well_id: str, b: WellUpdate, db=Depends(get_db), u=Depends(current_user)):
    if u["role"] not in ("manager","director","admin"): raise HTTPException(403, "Недостаточно прав")
    r = db.execute("SELECT code FROM wells WHERE id=?", (well_id,)).fetchone()
    if not r: raise HTTPException(404, "Скважина не найдена")
    upd = {k: v for k, v in b.dict(exclude_none=True).items()}
    n = now_str(); upd["updated_at"] = n
    db.execute(f"UPDATE wells SET {', '.join(f'{k}=?' for k in upd)} WHERE id=?", list(upd.values())+[well_id])
    db.execute("INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
               (str(uuid.uuid4()),f"{u['name']} ({u['role']})","Обновил скважину",r["code"],n))
    return well_row(db.execute("SELECT * FROM wells WHERE id=?", (well_id,)).fetchone(), db)

@app.delete("/wells/{well_id}")
def wells_delete(well_id: str, db=Depends(get_db), u=Depends(current_user)):
    if u["role"] not in ("director","admin"): raise HTTPException(403, "Недостаточно прав")
    r = db.execute("SELECT code FROM wells WHERE id=?", (well_id,)).fetchone()
    if not r: raise HTTPException(404, "Скважина не найдена")
    db.execute("INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
               (str(uuid.uuid4()),f"{u['name']} ({u['role']})","Удалил скважину",r["code"],now_str()))
    db.execute("DELETE FROM wells WHERE id=?", (well_id,))
    return {"ok": True}

# ── Routes: Reports ───────────────────────────────────────────────────────────
@app.get("/reports")
def reports_list(q: str = "", status: str = "all", db=Depends(get_db), u=Depends(current_user)):
    sql = "SELECT * FROM reports WHERE 1=1"; params = []
    if u["role"] == "operator": sql += " AND operator_id=?"; params.append(u["id"])
    if status != "all": sql += " AND status=?"; params.append(status)
    if q: sql += " AND (id LIKE ? OR well_id LIKE ?)"; params += [f"%{q}%", f"%{q}%"]
    return [report_row(r, db) for r in db.execute(sql+" ORDER BY created_at DESC", params).fetchall()]

@app.get("/reports/pending")
def reports_pending(db=Depends(get_db), u=Depends(current_user)):
    if u["role"] not in ("manager","director","admin"): raise HTTPException(403, "Недостаточно прав")
    return [report_row(r, db) for r in db.execute("SELECT * FROM reports WHERE status='pending' ORDER BY created_at DESC").fetchall()]

@app.post("/reports")
def reports_create(b: ReportCreate, db=Depends(get_db), u=Depends(current_user)):
    if not db.execute("SELECT id FROM wells WHERE id=?", (b.well_id,)).fetchone():
        raise HTTPException(404, "Скважина не найдена")
    score, summary, flag = ai_score(b)
    rid = str(uuid.uuid4()); n = now_str()
    st = "flagged" if flag else "pending"
    db.execute("INSERT INTO reports(id,well_id,operator_id,status,ai_score,summary,flag,temperature,production24h,tubing_internal_p,tubing_external_p,annulus_p,pump_strokes,comment,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (rid,b.well_id,u["id"],st,score,summary,flag,b.temperature,b.production24h,b.tubing_internal_p,b.tubing_external_p,b.annulus_p,b.pump_strokes,b.comment,n))
    if flag:
        db.execute("INSERT INTO notifications(id,user_id,icon,title,body,tone,unread,created_at) VALUES(?,?,?,?,?,?,1,?)",
                   (str(uuid.uuid4()),u["id"],"alert","AI: Аномалия обнаружена",flag,"warning",n))
    db.execute("INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
               (str(uuid.uuid4()),f"{u['name']} ({u['role']})","Создал отчёт",b.well_id,n))
    return report_row(db.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone(), db)

@app.get("/reports/{report_id}")
def reports_get(report_id: str, db=Depends(get_db), u=Depends(current_user)):
    r = db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    if not r: raise HTTPException(404, "Отчёт не найден")
    return report_row(r, db)

@app.post("/reports/{report_id}/review")
def reports_review(report_id: str, b: ReportReview, db=Depends(get_db), u=Depends(current_user)):
    if u["role"] not in ("manager","director","admin"): raise HTTPException(403, "Недостаточно прав")
    r = db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    if not r: raise HTTPException(404, "Отчёт не найден")
    if b.status not in ("approved","rejected"): raise HTTPException(400, "Неверный статус")
    n = now_str()
    db.execute("UPDATE reports SET status=?,reviewed_at=?,reviewed_by=? WHERE id=?", (b.status,n,u["id"],report_id))
    tone = "success" if b.status=="approved" else "destructive"
    title = "Отчёт одобрен" if b.status=="approved" else "Отчёт отклонён"
    db.execute("INSERT INTO notifications(id,user_id,icon,title,body,tone,unread,created_at) VALUES(?,?,?,?,?,?,1,?)",
               (str(uuid.uuid4()),r["operator_id"],"check" if b.status=="approved" else "x",title,b.comment or "",tone,n))
    db.execute("INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
               (str(uuid.uuid4()),f"{u['name']} ({u['role']})",f"{'Одобрил' if b.status=='approved' else 'Отклонил'} отчёт",report_id,n))
    return report_row(db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone(), db)

@app.delete("/reports/{report_id}")
def reports_delete(report_id: str, db=Depends(get_db), u=Depends(current_user)):
    r = db.execute("SELECT operator_id FROM reports WHERE id=?", (report_id,)).fetchone()
    if not r: raise HTTPException(404, "Отчёт не найден")
    if u["role"] not in ("manager","director","admin") and r["operator_id"] != u["id"]:
        raise HTTPException(403, "Недостаточно прав")
    db.execute("DELETE FROM reports WHERE id=?", (report_id,))
    return {"ok": True}

# ── Routes: Users ─────────────────────────────────────────────────────────────
@app.get("/users")
def users_list(db=Depends(get_db), u=Depends(current_user)):
    if u["role"] not in ("manager","director","admin"): raise HTTPException(403, "Недостаточно прав")
    return [u_out(dict(r)) for r in db.execute("SELECT * FROM users ORDER BY name").fetchall()]

@app.post("/users")
def users_create(b: UserCreate, db=Depends(get_db), u=Depends(current_user)):
    if u["role"] != "admin": raise HTTPException(403, "Только администратор")
    if db.execute("SELECT id FROM users WHERE email=?", (b.email,)).fetchone():
        raise HTTPException(400, "Email уже используется")
    uid = str(uuid.uuid4())
    pw = bcrypt.hashpw(b.password.encode(), bcrypt.gensalt()).decode()
    db.execute("INSERT INTO users(id,name,email,hashed_password,role,position,region,active) VALUES(?,?,?,?,?,?,?,1)",
               (uid,b.name,b.email,pw,b.role,b.position,b.region))
    return u_out(dict(db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()))

@app.put("/users/{user_id}")
def users_update(user_id: str, b: UserUpdate, db=Depends(get_db), u=Depends(current_user)):
    if u["role"] != "admin" and u["id"] != user_id: raise HTTPException(403, "Недостаточно прав")
    r = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not r: raise HTTPException(404, "Пользователь не найден")
    upd = {k: v for k, v in b.dict(exclude_none=True).items()}
    if "password" in upd: upd["hashed_password"] = bcrypt.hashpw(upd.pop("password").encode(), bcrypt.gensalt()).decode()
    if "active" in upd: upd["active"] = 1 if upd["active"] else 0
    if upd:
        db.execute(f"UPDATE users SET {', '.join(f'{k}=?' for k in upd)} WHERE id=?", list(upd.values())+[user_id])
    return u_out(dict(db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()))

@app.delete("/users/{user_id}")
def users_delete(user_id: str, db=Depends(get_db), u=Depends(current_user)):
    if u["role"] != "admin": raise HTTPException(403, "Только администратор")
    if not db.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone():
        raise HTTPException(404, "Пользователь не найден")
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    return {"ok": True}

# ── Routes: Notifications ─────────────────────────────────────────────────────
@app.get("/notifications")
def notifs_list(db=Depends(get_db), u=Depends(current_user)):
    rows = db.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC", (u["id"],)).fetchall()
    return [{"id":r["id"],"icon":r["icon"],"title":r["title"],"body":r["body"],"tone":r["tone"],"unread":bool(r["unread"]),"created_at":r["created_at"]} for r in rows]

@app.post("/notifications/read-all")
def notifs_read_all(db=Depends(get_db), u=Depends(current_user)):
    db.execute("UPDATE notifications SET unread=0 WHERE user_id=?", (u["id"],))
    return {"ok": True}

@app.post("/notifications/{notif_id}/read")
def notifs_read(notif_id: str, db=Depends(get_db), u=Depends(current_user)):
    db.execute("UPDATE notifications SET unread=0 WHERE id=? AND user_id=?", (notif_id, u["id"]))
    return {"ok": True}

# ── Routes: Calendar ──────────────────────────────────────────────────────────
@app.get("/calendar")
def cal_list(db=Depends(get_db), u=Depends(current_user)):
    rows = db.execute("SELECT * FROM calendar_events ORDER BY date").fetchall()
    return [{"id":r["id"],"title":r["title"],"date":r["date"],"event_type":r["event_type"],"created_by":r["created_by"]} for r in rows]

@app.post("/calendar")
def cal_create(b: CalEventCreate, db=Depends(get_db), u=Depends(current_user)):
    eid = str(uuid.uuid4()); n = now_str()
    db.execute("INSERT INTO calendar_events(id,title,date,event_type,created_by,created_at) VALUES(?,?,?,?,?,?)",
               (eid,b.title,b.date,b.event_type,u["id"],n))
    r = db.execute("SELECT * FROM calendar_events WHERE id=?", (eid,)).fetchone()
    return {"id":r["id"],"title":r["title"],"date":r["date"],"event_type":r["event_type"],"created_by":r["created_by"]}

@app.delete("/calendar/{event_id}")
def cal_delete(event_id: str, db=Depends(get_db), u=Depends(current_user)):
    db.execute("DELETE FROM calendar_events WHERE id=?", (event_id,))
    return {"ok": True}

# ── Routes: Dashboard ─────────────────────────────────────────────────────────
@app.get("/dashboard/stats")
def dashboard_stats(db=Depends(get_db), u=Depends(current_user)):
    active_w = db.execute("SELECT COUNT(*) FROM wells WHERE status='active'").fetchone()[0]
    warning_w = db.execute("SELECT COUNT(*) FROM wells WHERE status='warning'").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM reports WHERE status='pending'").fetchone()[0]
    flagged = db.execute("SELECT COUNT(*) FROM reports WHERE status='flagged'").fetchone()[0]
    prod = db.execute("SELECT COALESCE(SUM(production24h),0) FROM wells WHERE status='active'").fetchone()[0]
    now = datetime.utcnow()
    trend = [{"day":(now-timedelta(days=i)).strftime("%d.%m"),"oil":round(prod*(0.85+(i%3)*0.05),1),"gas":round(prod*0.1*(0.9+(i%4)*0.03),1)} for i in range(6,-1,-1)]
    statuses = [{"status":r["status"],"count":r["cnt"]} for r in db.execute("SELECT status, COUNT(*) as cnt FROM wells GROUP BY status").fetchall()]
    return {"active_wells":active_w,"warning_wells":warning_w,"pending_reports":pending,"flagged_reports":flagged,
            "total_production":round(prod,1),"production_trend":trend,"well_statuses":statuses}

# ── Routes: Audit ─────────────────────────────────────────────────────────────
@app.get("/audit")
def audit_list(db=Depends(get_db), u=Depends(current_user)):
    if u["role"] not in ("manager","director","admin"): raise HTTPException(403, "Недостаточно прав")
    rows = db.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100").fetchall()
    return [{"id":r["id"],"who":r["who"],"action":r["action"],"target":r["target"],"created_at":r["created_at"]} for r in rows]

# ── Routes: AI ────────────────────────────────────────────────────────────────
@app.post("/ai/chat")
def ai_chat(b: AIChatReq, db=Depends(get_db), u=Depends(current_user)):
    msg = b.message.lower()
    n = db.execute("SELECT COUNT(*) FROM wells").fetchone()[0]
    active = db.execute("SELECT COUNT(*) FROM wells WHERE status='active'").fetchone()[0]
    warning = db.execute("SELECT COUNT(*) FROM wells WHERE status='warning'").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM reports WHERE status='pending'").fetchone()[0]
    flagged = db.execute("SELECT COUNT(*) FROM reports WHERE status='flagged'").fetchone()[0]
    prod = db.execute("SELECT COALESCE(SUM(production24h),0) FROM wells WHERE status='active'").fetchone()[0]
    if any(k in msg for k in ("скважин","well")):
        return {"reply":f"На платформе {n} скважин. {active} активных, {warning} требуют внимания.","suggestions":["Показать карту скважин","Отчёты по скважинам"]}
    if any(k in msg for k in ("добыч","production")):
        return {"reply":f"Суммарная суточная добыча: {prod:.0f} т/сут.","suggestions":["KPI дашборд","Детализация по скважинам"]}
    if any(k in msg for k in ("отчёт","report")):
        return {"reply":f"Ожидают проверки {pending} отчётов. {flagged} помечены AI как аномальные.","suggestions":["Согласования","Создать отчёт"]}
    if any(k in msg for k in ("аномал",)):
        return {"reply":f"AI выявил {flagged} аномалий. Проверьте скважины со статусом warning.","suggestions":["Карта скважин","Согласования"]}
    if any(k in msg for k in ("привет","hello","здравствуй")):
        return {"reply":"Привет! Я AI-ассистент MUNAI. Спросите о скважинах, добыче или отчётах.","suggestions":["Статистика добычи","Статус скважин","Ожидающие отчёты"]}
    return {"reply":"Я обрабатываю данные MUNAI. Спросите о скважинах, добыче или аномалиях.","suggestions":["Статистика добычи","Статус скважин"]}

@app.get("/ai/insights")
def ai_insights(db=Depends(get_db), u=Depends(current_user)):
    w = db.execute("SELECT COUNT(*) FROM wells WHERE status='warning'").fetchone()[0]
    f = db.execute("SELECT COUNT(*) FROM reports WHERE status='flagged'").fetchone()[0]
    return {"insights":[{"type":"warning","message":f"{w} скважин требуют внимания"},{"type":"info","message":f"{f} отчётов помечены AI"}]}

# ── Vercel handler ────────────────────────────────────────────────────────────
handler = Mangum(app, lifespan="off")
