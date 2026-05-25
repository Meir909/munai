"""Vercel serverless entry point — wraps FastAPI app with Mangum."""
import sys
import os

# Add api directory to path so app package is importable
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.config import settings
from app.database import engine, SessionLocal
from app import models
from app.seed import seed_db
from app.routers import auth, wells, reports, users, notifications, calendar, dashboard, audit, ai

# Create all tables on cold start
models.Base.metadata.create_all(bind=engine)

# Seed once
_seeded = False
def _seed():
    global _seeded
    if _seeded:
        return
    db = SessionLocal()
    try:
        seed_db(db)
        _seeded = True
    finally:
        db.close()

_seed()

app = FastAPI(
    title="MUNAI API",
    description="AI Digital Oilfield Operations Platform",
    version="1.0.0",
    root_path="/api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(wells.router)
app.include_router(reports.router)
app.include_router(users.router)
app.include_router(notifications.router)
app.include_router(calendar.router)
app.include_router(dashboard.router)
app.include_router(audit.router)
app.include_router(ai.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "MUNAI API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# Vercel handler
handler = Mangum(app, lifespan="off")
