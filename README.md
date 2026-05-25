# MUNAI — AI Digital Oilfield Operations Platform

Full-stack enterprise application: React frontend + FastAPI backend + SQLite database.

## Quick Start

### 1. Start Backend
```
Double-click: START_BACKEND.bat
```
Or manually:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**  
API docs: **http://localhost:8000/docs**

### 2. Start Frontend
```
Double-click: START_FRONTEND.bat
```
Or manually:
```bash
cd munai-digital-oilfield-ops-main
npm install
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## Demo Accounts (password: `demo`)

| Role | Email |
|------|-------|
| Operator | operator@munai.kz |
| Manager | manager@munai.kz |
| Director | director@munai.kz |
| Admin | admin@munai.kz |

---

## Architecture

```
Frontend (React + TanStack)
    ↕ REST API calls
Backend (FastAPI + Python)
    ↕ SQLAlchemy ORM
Database (SQLite → PostgreSQL-ready)
```

### Backend Structure
```
backend/
├── main.py              # FastAPI app entry
├── requirements.txt     # Python deps
├── .env                 # Environment config
├── munai.db             # SQLite DB (auto-created)
└── app/
    ├── config.py        # Settings
    ├── database.py      # DB connection
    ├── models.py        # SQLAlchemy models
    ├── schemas.py       # Pydantic schemas
    ├── auth.py          # JWT authentication
    ├── seed.py          # Demo data seeder
    └── routers/
        ├── auth.py      # Login/register/me
        ├── wells.py     # Well CRUD
        ├── reports.py   # Report CRUD + AI scoring
        ├── users.py     # User management
        ├── notifications.py
        ├── calendar.py
        ├── dashboard.py # Stats & trends
        ├── audit.py     # Audit log
        └── ai.py        # AI chat & insights
```

### Frontend Structure
```
munai-digital-oilfield-ops-main/src/
├── lib/
│   ├── api.ts       # All API calls (centralized)
│   ├── store.ts     # Zustand state management
│   ├── session.tsx  # Auth-aware session hook
│   └── ...
└── routes/
    ├── login.tsx          # Real auth login
    ├── register.tsx       # Real registration
    ├── app.dashboard.tsx  # Live dashboard stats
    ├── app.wells.tsx      # Well CRUD with modals
    ├── app.reports.tsx    # Report list + filters
    ├── app.reports.new.tsx # Create report → AI scoring
    ├── app.approvals.tsx  # Approve/reject reports
    ├── app.notifications.tsx # Live notifications
    ├── app.ai.tsx         # AI chat assistant
    ├── app.admin.tsx      # User management CRUD
    ├── app.calendar.tsx   # Event management
    ├── app.audit.tsx      # Audit log
    ├── app.map.tsx        # Well map (real data)
    └── app.profile.tsx    # Profile editing
```

## Features

- **Real authentication** — JWT tokens, protected routes, role-based UI
- **Full CRUD** — Wells, Reports, Users, Events
- **AI scoring** — Automatic anomaly detection on report submission
- **Live notifications** — Auto-refreshed every 30s, mark as read
- **Role-based access** — Operator ≠ Manager ≠ Director ≠ Admin
- **Audit log** — Every action logged automatically
- **Responsive** — Works on desktop, tablet, mobile

## Production Deployment

Change `DATABASE_URL` in `backend/.env` to PostgreSQL:
```
DATABASE_URL=postgresql://user:password@host:5432/munai
```

Change `VITE_API_URL` in `munai-digital-oilfield-ops-main/.env` to production URL:
```
VITE_API_URL=https://api.yourdomain.com/api
```
