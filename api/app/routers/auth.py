import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection
from app.database import get_db
from app import schemas
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _row_to_user(row) -> schemas.UserOut:
    return schemas.UserOut(
        id=row["id"], name=row["name"], email=row["email"],
        role=row["role"], position=row["position"] or "",
        region=row["region"] or "", active=bool(row["active"])
    )


@router.post("/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest, db: Connection = Depends(get_db)):
    row = db.execute("SELECT * FROM users WHERE email=?", (body.email,)).fetchone()
    if not row or not verify_password(body.password, row["hashed_password"]):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not row["active"]:
        raise HTTPException(status_code=403, detail="Аккаунт деактивирован")
    token = create_access_token({"sub": row["id"]})
    return schemas.TokenResponse(access_token=token, token_type="bearer", user=_row_to_user(row))


@router.post("/register", response_model=schemas.TokenResponse)
def register(body: schemas.RegisterRequest, db: Connection = Depends(get_db)):
    existing = db.execute("SELECT id FROM users WHERE email=?", (body.email,)).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Email уже используется")
    uid = str(uuid.uuid4())
    db.execute(
        "INSERT INTO users(id,name,email,hashed_password,role,position,region,active) VALUES(?,?,?,?,?,?,?,1)",
        (uid, body.name, body.email, hash_password(body.password), body.role, body.position, body.region)
    )
    row = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    token = create_access_token({"sub": uid})
    return schemas.TokenResponse(access_token=token, token_type="bearer", user=_row_to_user(row))


@router.get("/me", response_model=schemas.UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user
