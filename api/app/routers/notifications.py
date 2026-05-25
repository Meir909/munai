from fastapi import APIRouter, Depends
from sqlite3 import Connection
from app.database import get_db
from app import schemas
from app.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _row_to_out(row) -> schemas.NotificationOut:
    return schemas.NotificationOut(
        id=row["id"], icon=row["icon"] or "info",
        title=row["title"], body=row["body"] or "",
        tone=row["tone"] or "info", unread=bool(row["unread"]),
        created_at=row["created_at"]
    )


@router.get("", response_model=list[schemas.NotificationOut])
def list_notifications(db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    rows = db.execute(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC", (current_user.id,)
    ).fetchall()
    return [_row_to_out(r) for r in rows]


@router.post("/{notif_id}/read")
def mark_read(notif_id: str, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    db.execute(
        "UPDATE notifications SET unread=0 WHERE id=? AND user_id=?", (notif_id, current_user.id)
    )
    return {"ok": True}


@router.post("/read-all")
def mark_all_read(db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    db.execute("UPDATE notifications SET unread=0 WHERE user_id=?", (current_user.id,))
    return {"ok": True}
