import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlite3 import Connection
from app.database import get_db
from app import schemas
from app.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


def _ai_score(data: schemas.ReportCreate) -> tuple[int, str, str | None]:
    score = 100
    flag = None
    issues = []
    if data.temperature and data.temperature > 90:
        score -= 30
        issues.append("Критически высокая температура")
        flag = "Аномалия температуры"
    elif data.temperature and data.temperature > 80:
        score -= 15
        issues.append("Повышенная температура")
    if data.production24h and data.production24h < 10:
        score -= 20
        issues.append("Низкая суточная добыча")
    if data.tubing_internal_p and data.tubing_internal_p > 160:
        score -= 25
        issues.append("Высокое давление в НКТ")
        flag = flag or "Превышение давления"
    if data.pump_strokes and data.pump_strokes < 3:
        score -= 20
        issues.append("Низкая частота качания")
    score = max(0, score)
    summary = "Параметры в норме." if not issues else "Выявлено: " + "; ".join(issues) + "."
    return score, summary, flag


def _row_to_out(row, db: Connection) -> schemas.ReportOut:
    well = db.execute("SELECT code, name FROM wells WHERE id=?", (row["well_id"],)).fetchone()
    op = db.execute("SELECT name FROM users WHERE id=?", (row["operator_id"],)).fetchone()
    return schemas.ReportOut(
        id=row["id"], well_id=row["well_id"],
        well_code=well["code"] if well else None,
        well_name=well["name"] if well else None,
        operator_id=row["operator_id"],
        operator_name=op["name"] if op else None,
        status=row["status"], ai_score=row["ai_score"],
        summary=row["summary"] or "", flag=row["flag"],
        temperature=row["temperature"], production24h=row["production24h"],
        tubing_internal_p=row["tubing_internal_p"], tubing_external_p=row["tubing_external_p"],
        annulus_p=row["annulus_p"], pump_strokes=row["pump_strokes"],
        comment=row["comment"], created_at=row["created_at"], reviewed_at=row["reviewed_at"],
    )


@router.get("", response_model=list[schemas.ReportOut])
def list_reports(
    q: str = Query(default=""),
    status: str = Query(default="all"),
    db: Connection = Depends(get_db),
    current_user=Depends(get_current_user),
):
    sql = "SELECT r.* FROM reports r WHERE 1=1"
    params = []
    if current_user.role == "operator":
        sql += " AND r.operator_id=?"
        params.append(current_user.id)
    if status != "all":
        sql += " AND r.status=?"
        params.append(status)
    if q:
        sql += " AND (r.id LIKE ? OR r.well_id LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY r.created_at DESC"
    rows = db.execute(sql, params).fetchall()
    return [_row_to_out(r, db) for r in rows]


@router.get("/pending", response_model=list[schemas.ReportOut])
def pending_reports(db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    rows = db.execute("SELECT * FROM reports WHERE status='pending' ORDER BY created_at DESC").fetchall()
    return [_row_to_out(r, db) for r in rows]


@router.get("/{report_id}", response_model=schemas.ReportOut)
def get_report(report_id: str, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    row = db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    return _row_to_out(row, db)


@router.post("", response_model=schemas.ReportOut)
def create_report(body: schemas.ReportCreate, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    well = db.execute("SELECT id FROM wells WHERE id=?", (body.well_id,)).fetchone()
    if not well:
        raise HTTPException(status_code=404, detail="Скважина не найдена")
    score, summary, flag = _ai_score(body)
    rid = str(uuid.uuid4())
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    status = "flagged" if flag else "pending"
    db.execute(
        "INSERT INTO reports(id,well_id,operator_id,status,ai_score,summary,flag,"
        "temperature,production24h,tubing_internal_p,tubing_external_p,annulus_p,"
        "pump_strokes,comment,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (rid, body.well_id, current_user.id, status, score, summary, flag,
         body.temperature, body.production24h, body.tubing_internal_p,
         body.tubing_external_p, body.annulus_p, body.pump_strokes, body.comment, now)
    )
    if flag:
        db.execute(
            "INSERT INTO notifications(id,user_id,icon,title,body,tone,unread,created_at) VALUES(?,?,?,?,?,?,1,?)",
            (str(uuid.uuid4()), current_user.id, "alert", f"AI: Аномалия обнаружена", flag, "warning", now)
        )
    db.execute(
        "INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()), f"{current_user.name} ({current_user.role})", "Создал отчёт", body.well_id, now)
    )
    row = db.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
    return _row_to_out(row, db)


@router.post("/{report_id}/review", response_model=schemas.ReportOut)
def review_report(report_id: str, body: schemas.ReportReview, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    row = db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Статус должен быть approved или rejected")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "UPDATE reports SET status=?, reviewed_at=?, reviewed_by=? WHERE id=?",
        (body.status, now, current_user.id, report_id)
    )
    tone = "success" if body.status == "approved" else "destructive"
    title = "Отчёт одобрен" if body.status == "approved" else "Отчёт отклонён"
    db.execute(
        "INSERT INTO notifications(id,user_id,icon,title,body,tone,unread,created_at) VALUES(?,?,?,?,?,?,1,?)",
        (str(uuid.uuid4()), row["operator_id"], "check" if body.status == "approved" else "x",
         title, body.comment or "", tone, now)
    )
    db.execute(
        "INSERT INTO audit_logs(id,who,action,target,created_at) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()), f"{current_user.name} ({current_user.role})",
         "Одобрил отчёт" if body.status == "approved" else "Отклонил отчёт", report_id, now)
    )
    row = db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    return _row_to_out(row, db)


@router.delete("/{report_id}")
def delete_report(report_id: str, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    row = db.execute("SELECT operator_id FROM reports WHERE id=?", (report_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    if current_user.role not in ("manager", "director", "admin") and row["operator_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    db.execute("DELETE FROM reports WHERE id=?", (report_id,))
    return {"ok": True}
