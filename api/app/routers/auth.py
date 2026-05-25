import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.models import AuditLog

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.TokenResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")
    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт отключён")
    token = create_access_token({"sub": user.id, "role": user.role})
    return schemas.TokenResponse(access_token=token, user=schemas.UserOut.model_validate(user))


@router.post("/register", response_model=schemas.TokenResponse)
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email уже используется")
    user = models.User(
        id=str(uuid.uuid4()),
        name=req.name,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=req.role,
        position=req.position,
        region=req.region,
    )
    db.add(user)
    audit = AuditLog(id=str(uuid.uuid4()), who="Система", action="Зарегистрировал пользователя", target=req.email)
    db.add(audit)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.id, "role": user.role})
    return schemas.TokenResponse(access_token=token, user=schemas.UserOut.model_validate(user))


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return schemas.UserOut.model_validate(current_user)
