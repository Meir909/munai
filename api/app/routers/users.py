import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, hash_password
from app.models import AuditLog

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return [schemas.UserOut.model_validate(u) for u in db.query(models.User).order_by(models.User.name).all()]


@router.post("", response_model=schemas.UserOut)
def create_user(
    body: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только администратор может создавать пользователей")
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email уже используется")
    user = models.User(
        id=str(uuid.uuid4()),
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
        position=body.position,
        region=body.region,
    )
    db.add(user)
    audit = AuditLog(id=str(uuid.uuid4()), who=f"{current_user.name} (admin)", action="Создал пользователя", target=body.email)
    db.add(audit)
    db.commit()
    db.refresh(user)
    return schemas.UserOut.model_validate(user)


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: str,
    body: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    data = body.model_dump(exclude_none=True)
    if "password" in data:
        user.hashed_password = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(user, k, v)
    audit = AuditLog(id=str(uuid.uuid4()), who=f"{current_user.name} ({current_user.role})", action="Обновил пользователя", target=user.email)
    db.add(audit)
    db.commit()
    db.refresh(user)
    return schemas.UserOut.model_validate(user)


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только администратор может удалять пользователей")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    audit = AuditLog(id=str(uuid.uuid4()), who=f"{current_user.name} (admin)", action="Удалил пользователя", target=user.email)
    db.add(audit)
    db.delete(user)
    db.commit()
    return {"ok": True}
