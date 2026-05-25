import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.models import AuditLog

router = APIRouter(prefix="/wells", tags=["wells"])


def well_to_out(w: models.Well) -> schemas.WellOut:
    last_report = None
    if w.reports:
        latest = max(w.reports, key=lambda r: r.created_at)
        delta = datetime.utcnow() - latest.created_at
        hours = int(delta.total_seconds() // 3600)
        if hours < 1:
            last_report = "Менее часа назад"
        elif hours < 24:
            last_report = f"{hours}ч назад"
        else:
            last_report = f"{hours // 24}д назад"

    return schemas.WellOut(
        id=w.id,
        code=w.code,
        name=w.name,
        status=w.status,
        product=w.product,
        production24h=w.production24h,
        temperature=w.temperature,
        tubing_internal_p=w.tubing_internal_p,
        tubing_external_p=w.tubing_external_p,
        annulus_p=w.annulus_p,
        pump_strokes=w.pump_strokes,
        lat=w.lat,
        lng=w.lng,
        operator_id=w.operator_id,
        manager_id=w.manager_id,
        operator_name=w.operator.name if w.operator else None,
        manager_name=w.manager.name if w.manager else None,
        last_report=last_report,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )


@router.get("", response_model=list[schemas.WellOut])
def list_wells(
    q: str = Query(default="", description="Search query"),
    status: str = Query(default="all"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Well)
    if status != "all":
        query = query.filter(models.Well.status == status)
    if q:
        query = query.filter(
            (models.Well.code.ilike(f"%{q}%")) | (models.Well.name.ilike(f"%{q}%"))
        )
    wells = query.order_by(models.Well.code).all()
    return [well_to_out(w) for w in wells]


@router.get("/{well_id}", response_model=schemas.WellOut)
def get_well(well_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    w = db.query(models.Well).filter(models.Well.id == well_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Скважина не найдена")
    return well_to_out(w)


@router.post("", response_model=schemas.WellOut)
def create_well(
    body: schemas.WellCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if db.query(models.Well).filter(models.Well.code == body.code).first():
        raise HTTPException(status_code=400, detail="Скважина с таким кодом уже существует")
    w = models.Well(id=str(uuid.uuid4()), **body.model_dump())
    db.add(w)
    audit = AuditLog(id=str(uuid.uuid4()), who=f"{current_user.name} ({current_user.role})", action="Создал скважину", target=body.code)
    db.add(audit)
    db.commit()
    db.refresh(w)
    return well_to_out(w)


@router.put("/{well_id}", response_model=schemas.WellOut)
def update_well(
    well_id: str,
    body: schemas.WellUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    w = db.query(models.Well).filter(models.Well.id == well_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Скважина не найдена")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(w, field, value)
    w.updated_at = datetime.utcnow()
    audit = AuditLog(id=str(uuid.uuid4()), who=f"{current_user.name} ({current_user.role})", action="Обновил скважину", target=w.code)
    db.add(audit)
    db.commit()
    db.refresh(w)
    return well_to_out(w)


@router.delete("/{well_id}")
def delete_well(
    well_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in ("director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    w = db.query(models.Well).filter(models.Well.id == well_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Скважина не найдена")
    audit = AuditLog(id=str(uuid.uuid4()), who=f"{current_user.name} ({current_user.role})", action="Удалил скважину", target=w.code)
    db.add(audit)
    db.delete(w)
    db.commit()
    return {"ok": True}
