import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

# Ensure parent directory exists (needed for /tmp/munai.db on Vercel)
db_url = settings.DATABASE_URL
if "sqlite" in db_url:
    db_path = db_url.replace("sqlite:////", "/").replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir and db_dir != "." and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
