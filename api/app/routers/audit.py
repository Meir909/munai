from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection
from app.database import get_db
from app import schemas
from app.auth import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[schemas.AuditLogOut])
def list_audit(db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    rows = db.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100").fetchall()
    return [schemas.AuditLogOut(id=r["id"], who=r["who"], action=r["action"], target=r["target"], created_at=r["created_at"]) for r in rows]
