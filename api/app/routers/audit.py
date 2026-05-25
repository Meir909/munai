from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[schemas.AuditLogOut])
def list_audit(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    logs = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(100).all()
    return [schemas.AuditLogOut.model_validate(l) for l in logs]
