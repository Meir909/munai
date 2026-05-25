import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("", response_model=list[schemas.CalendarEventOut])
def list_events(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    events = db.query(models.CalendarEvent).order_by(models.CalendarEvent.date).all()
    return [schemas.CalendarEventOut.model_validate(e) for e in events]


@router.post("", response_model=schemas.CalendarEventOut)
def create_event(
    body: schemas.CalendarEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    e = models.CalendarEvent(
        id=str(uuid.uuid4()),
        title=body.title,
        date=body.date,
        event_type=body.event_type,
        created_by=current_user.id,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return schemas.CalendarEventOut.model_validate(e)


@router.delete("/{event_id}")
def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    e = db.query(models.CalendarEvent).filter(models.CalendarEvent.id == event_id).first()
    if e:
        db.delete(e)
        db.commit()
    return {"ok": True}
