import uuid
import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.models import AuditLog, Notification

router = APIRouter(prefix="/reports", tags=["reports"])


def _ai_score(body: schemas.ReportCreate) -> tuple[int, str | None, str]:
    """Simple rule-based AI scoring matching frontend demo logic."""
    score = 85
    flag = None
    issues = []

    if body.temperature and body.temperature > 90:
        score -= 40
        flag = "Аномалия температуры"
        issues.append(f"Температура {body.temperature}°C выше нормы")
    elif body.temperature and body.temperature > 80:
        score -= 15
        issues.append(f"Температура повышена до {body.temperature}°C")

    if body.tubing_internal_p and body.tubing_internal_p > 160:
        score -= 20
        flag = flag or "Высокое давление НКТ"
        issues.append("Давление НКТ критическое")

    if body.production24h and body.production24h < 10:
        score -= 25
        flag = flag or "Низкая добыча"
        issues.append("Добыча значительно ниже нормы")

    score = max(0, min(100, score + random.randint(-5, 5)))

    if issues:
        summary = ". ".join(issues) + "."
    else:
        summary = "Параметры в норме, добыча стабильна."

    status = "flagged" if flag else "pending"
    return score, flag, summary, status


def report_to_out(r: models.Report) -> schemas.ReportOut:
    return schemas.ReportOut(
        id=r.id,
        well_id=r.well_id,
        well_code=r.well.code if r.well else None,
        well_name=r.well.name if r.well else None,
        operator_id=r.operator_id,
        operator_name=r.user.name if r.user else None,
        status=r.status,
        ai_score=r.ai_score,
        summary=r.summary,
        flag=r.flag,
        temperature=r.temperature,
        production24h=r.production24h,
        tubing_internal_p=r.tubing_internal_p,
        tubing_external_p=r.tubing_external_p,
        annulus_p=r.annulus_p,
        pump_strokes=r.pump_strokes,
        comment=r.comment,
        created_at=r.created_at,
        reviewed_at=r.reviewed_at,
    )


@router.get("", response_model=list[schemas.ReportOut])
def list_reports(
    q: str = Query(default=""),
    status: str = Query(default="all"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Report)
    if current_user.role == "operator":
        query = query.filter(models.Report.operator_id == current_user.id)
    if status != "all":
        query = query.filter(models.Report.status == status)
    reports = query.order_by(models.Report.created_at.desc()).all()
    if q:
        reports = [r for r in reports if q.lower() in (r.well.code if r.well else "").lower() or q.lower() in (r.user.name if r.user else "").lower()]
    return [report_to_out(r) for r in reports]


@router.get("/pending", response_model=list[schemas.ReportOut])
def pending_reports(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    reports = db.query(models.Report).filter(
        models.Report.status.in_(["pending", "flagged"])
    ).order_by(models.Report.created_at.desc()).all()
    return [report_to_out(r) for r in reports]


@router.get("/{report_id}", response_model=schemas.ReportOut)
def get_report(report_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    r = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    return report_to_out(r)


@router.post("", response_model=schemas.ReportOut)
def create_report(
    body: schemas.ReportCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    well = db.query(models.Well).filter(models.Well.id == body.well_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Скважина не найдена")

    score, flag, summary, report_status = _ai_score(body)

    r = models.Report(
        id=str(uuid.uuid4()),
        well_id=body.well_id,
        operator_id=current_user.id,
        status=report_status,
        ai_score=score,
        summary=summary,
        flag=flag,
        temperature=body.temperature,
        production24h=body.production24h,
        tubing_internal_p=body.tubing_internal_p,
        tubing_external_p=body.tubing_external_p,
        annulus_p=body.annulus_p,
        pump_strokes=body.pump_strokes,
        comment=body.comment,
    )
    db.add(r)

    # Audit log
    audit = AuditLog(id=str(uuid.uuid4()), who=f"{current_user.name} ({current_user.role})", action="Создал отчёт", target=well.code)
    db.add(audit)

    # Notify manager if flagged
    if flag and well.manager_id:
        notif = Notification(
            id=str(uuid.uuid4()),
            user_id=well.manager_id,
            icon="alert",
            title=f"AI: Аномалия на {well.code}",
            body=f"{summary} (AI score: {score}/100)",
            tone="warning",
            unread=True,
        )
        db.add(notif)

        # Also notify the operator
        op_notif = Notification(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            icon="alert",
            title=f"AI обнаружил аномалию в {well.code}",
            body=f"{flag}: {summary}",
            tone="warning",
            unread=True,
        )
        db.add(op_notif)

    db.commit()
    db.refresh(r)
    return report_to_out(r)


@router.post("/{report_id}/review", response_model=schemas.ReportOut)
def review_report(
    report_id: str,
    body: schemas.ReportReview,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Статус должен быть approved или rejected")

    r = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Отчёт не найден")

    r.status = body.status
    r.reviewed_at = datetime.utcnow()
    r.reviewed_by = current_user.id

    action_ru = "Одобрил отчёт" if body.status == "approved" else "Отклонил отчёт"
    audit = AuditLog(id=str(uuid.uuid4()), who=f"{current_user.name} ({current_user.role})", action=action_ru, target=r.well.code if r.well else r.well_id)
    db.add(audit)

    # Notify the operator
    tone = "success" if body.status == "approved" else "destructive"
    title = f"Отчёт одобрен" if body.status == "approved" else "Отчёт отклонён"
    notif = Notification(
        id=str(uuid.uuid4()),
        user_id=r.operator_id,
        icon="check" if body.status == "approved" else "edit",
        title=title,
        body=f"Отчёт по {r.well.code if r.well else r.well_id} {action_ru.lower()}. {body.comment or ''}",
        tone=tone,
        unread=True,
    )
    db.add(notif)
    db.commit()
    db.refresh(r)
    return report_to_out(r)


@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    r = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    if current_user.role not in ("admin", "director") and r.operator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    db.delete(r)
    db.commit()
    return {"ok": True}
