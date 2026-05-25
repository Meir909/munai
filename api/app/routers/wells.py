import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlite3 import Connection
from app.database import get_db
from app import schemas
from app.auth import get_current_user

router = APIRouter(prefix="/wells", tags=["wells"])


def _last_report_label(created_at_str):
    if not created_at_str:
        return None
    try:
        ts = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
        delta = datetime.utcnow() - ts
        hours = int(delta.total_seconds() // 3600)
        if hours < 1:
            return "Менее часа назад"
        elif hours < 24:
            return f"{hours}ч назад"
        else:
            return f"{hours // 24}д назад"
    except Exception:
        return None


def _row_to_out(row, db: Connection) -> schemas.WellOut:
    op_name = None
    if row["operator_id"]:
        u = db.execute("SELECT name FROM users WHERE id=?", (row["operator_id"],)).fetchone()
        op_name = u["name"] if u else None
    mg_name = None
    if row["manager_id"]:
        u = db.execute("SELECT name FROM users WHERE id=?", (row["manager_id"],)).fetchone()
        mg_name = u["name"] if u else None
    last_r = db.execute(
        "SELECT created_at FROM reports WHERE well_id=? ORDER BY created_at DESC LIMIT 1", (row["id"],)
    ).fetchone()
    last_report = _last_report_label(last_r["created_at"] if last_r else None)
    return schemas.WellOut(
        id=row["id"], code=row["code"], name=row["name"],
        status=row["status"], product=row["product"],
        production24h=row["production24h"], temperature=row["temperature"],
        tubing_internal_p=row["tubing_internal_p"], tubing_external_p=row["tubing_external_p"],
        annulus_p=row["annulus_p"], pump_strokes=row["pump_strokes"],
        lat=row["lat"], lng=row["lng"],
        operator_id=row["operator_id"], manager_id=row["manager_id"],
        operator_name=op_name, manager_name=mg_name,
        last_report=last_report,
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


@router.get("", response_model=list[schemas.WellOut])
def list_wells(
    q: str = Query(default=""),
    status: str = Query(default="all"),
    db: Connection = Depends(get_db),
    current_user=Depends(get_current_user),
):
    sql = "SELECT * FROM wells WHERE 1=1"
    params = []
    if status != "all":
        sql += " AND status=?"
        params.append(status)
    if q:
        sql += " AND (code LIKE ? OR name LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY code"
    rows = db.execute(sql, params).fetchall()
    return [_row_to_out(r, db) for r in rows]


@router.get("/{well_id}", response_model=schemas.WellOut)
def get_well(well_id: str, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    row = db.execute("SELECT * FROM wells WHERE id=?", (well_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Скважина не найдена")
    return _row_to_out(row, db)


@router.post("", response_model=schemas.WellOut)
def create_well(body: schemas.WellCreate, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if db.execute("SELECT id FROM wells WHERE code=?", (body.code,)).fetchone():
        raise HTTPException(status_code=400, detail="Скважина с таким кодом уже существует")
    wid = str(uuid.uuid4())
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "INSERT INTO wells(id,code,name,status,product,production24h,temperature,"
        "tubing_internal_p,tubing_external_p,annulus_p,pump_strokes,lat,lng,"
        "operator_id,manager_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (wid, body.code, body.name, body.status, body.product, body.production24h,
         body.temperature, body.tubing_internal_p, body.tubing_external_p,
         body.annulus_p, body.pump_strokes, body.lat, body.lng,
         body.operator_id, body.manager_id, now, now)
    )
    db.execute(
        "INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()), f"{current_user.name} ({current_user.role})", "Создал скважину", body.code, now)
    )
    row = db.execute("SELECT * FROM wells WHERE id=?", (wid,)).fetchone()
    return _row_to_out(row, db)


@router.put("/{well_id}", response_model=schemas.WellOut)
def update_well(well_id: str, body: schemas.WellUpdate, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    row = db.execute("SELECT * FROM wells WHERE id=?", (well_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Скважина не найдена")
    updates = {k: v for k, v in body.dict(exclude_none=True).items()}
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    updates["updated_at"] = now
    set_clause = ", ".join(f"{k}=?" for k in updates)
    db.execute(f"UPDATE wells SET {set_clause} WHERE id=?", list(updates.values()) + [well_id])
    db.execute(
        "INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()), f"{current_user.name} ({current_user.role})", "Обновил скважину", row["code"], now)
    )
    row = db.execute("SELECT * FROM wells WHERE id=?", (well_id,)).fetchone()
    return _row_to_out(row, db)


@router.delete("/{well_id}")
def delete_well(well_id: str, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role not in ("director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    row = db.execute("SELECT code FROM wells WHERE id=?", (well_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Скважина не найдена")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()), f"{current_user.name} ({current_user.role})", "Удалил скважину", row["code"], now)
    )
    db.execute("DELETE FROM wells WHERE id=?", (well_id,))
    return {"ok": True}
