"""Vercel serverless entry point — wraps FastAPI app with Mangum."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.config import settings
from app.database import init_db, get_connection
from app.seed import seed_db
from app.routers import auth, wells, reports, users, notifications, calendar, dashboard, audit, ai

# Initialize DB schema and seed on cold start
init_db()
_conn = get_connection()
try:
    seed_db(_conn)
finally:
    _conn.close()

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


handler = Mangum(app, lifespan="off")
