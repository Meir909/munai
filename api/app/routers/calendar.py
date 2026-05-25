import uuid
from fastapi import APIRouter, Depends
from sqlite3 import Connection
from datetime import datetime
from app.database import get_db
from app import schemas
from app.auth import get_current_user

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _row_to_out(row) -> schemas.CalendarEventOut:
    return schemas.CalendarEventOut(
        id=row["id"], title=row["title"], date=row["date"],
        event_type=row["event_type"], created_by=row["created_by"]
    )


@router.get("", response_model=list[schemas.CalendarEventOut])
def list_events(db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    rows = db.execute("SELECT * FROM calendar_events ORDER BY date").fetchall()
    return [_row_to_out(r) for r in rows]


@router.post("", response_model=schemas.CalendarEventOut)
def create_event(body: schemas.CalendarEventCreate, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    eid = str(uuid.uuid4())
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "INSERT INTO calendar_events(id,title,date,event_type,created_by,created_at) VALUES(?,?,?,?,?,?)",
        (eid, body.title, body.date, body.event_type, current_user.id, now)
    )
    row = db.execute("SELECT * FROM calendar_events WHERE id=?", (eid,)).fetchone()
    return _row_to_out(row)


@router.delete("/{event_id}")
def delete_event(event_id: str, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    db.execute("DELETE FROM calendar_events WHERE id=?", (event_id,))
    return {"ok": True}
