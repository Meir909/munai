import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection
from app.database import get_db
from app import schemas
from app.auth import get_current_user, hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _row_to_user(row) -> schemas.UserOut:
    return schemas.UserOut(
        id=row["id"], name=row["name"], email=row["email"],
        role=row["role"], position=row["position"] or "",
        region=row["region"] or "", active=bool(row["active"])
    )


@router.get("", response_model=list[schemas.UserOut])
def list_users(db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role not in ("manager", "director", "admin"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    rows = db.execute("SELECT * FROM users ORDER BY name").fetchall()
    return [_row_to_user(r) for r in rows]


@router.post("", response_model=schemas.UserOut)
def create_user(body: schemas.UserCreate, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только администратор может создавать пользователей")
    if db.execute("SELECT id FROM users WHERE email=?", (body.email,)).fetchone():
        raise HTTPException(status_code=400, detail="Email уже используется")
    uid = str(uuid.uuid4())
    db.execute(
        "INSERT INTO users(id,name,email,hashed_password,role,position,region,active) VALUES(?,?,?,?,?,?,?,1)",
        (uid, body.name, body.email, hash_password(body.password), body.role, body.position, body.region)
    )
    row = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return _row_to_user(row)


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: str, body: schemas.UserUpdate, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role not in ("admin",) and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    updates = body.dict(exclude_none=True)
    if "password" in updates:
        updates["hashed_password"] = hash_password(updates.pop("password"))
    if "active" in updates:
        updates["active"] = 1 if updates["active"] else 0
    if not updates:
        return _row_to_user(row)
    set_clause = ", ".join(f"{k}=?" for k in updates)
    db.execute(f"UPDATE users SET {set_clause} WHERE id=?", list(updates.values()) + [user_id])
    row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return _row_to_user(row)


@router.delete("/{user_id}")
def delete_user(user_id: str, db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только администратор может удалять пользователей")
    if not db.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    return {"ok": True}
