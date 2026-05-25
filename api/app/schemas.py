from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "operator"
    position: str = ""
    region: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ── Users ─────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    position: str
    region: str
    active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "operator"
    position: str = ""
    region: str = ""


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    position: Optional[str] = None
    region: Optional[str] = None
    active: Optional[bool] = None
    password: Optional[str] = None


# ── Wells ─────────────────────────────────────────────────────────────────────

class WellOut(BaseModel):
    id: str
    code: str
    name: str
    status: str
    product: str
    production24h: float
    temperature: float
    tubing_internal_p: float
    tubing_external_p: float
    annulus_p: float
    pump_strokes: int
    lat: float
    lng: float
    operator_id: Optional[str] = None
    manager_id: Optional[str] = None
    operator_name: Optional[str] = None
    manager_name: Optional[str] = None
    last_report: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WellCreate(BaseModel):
    code: str
    name: str
    status: str = "active"
    product: str = "oil"
    production24h: float = 0.0
    temperature: float = 0.0
    tubing_internal_p: float = 0.0
    tubing_external_p: float = 0.0
    annulus_p: float = 0.0
    pump_strokes: int = 0
    lat: float = 50.0
    lng: float = 55.0
    operator_id: Optional[str] = None
    manager_id: Optional[str] = None


class WellUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    product: Optional[str] = None
    production24h: Optional[float] = None
    temperature: Optional[float] = None
    tubing_internal_p: Optional[float] = None
    tubing_external_p: Optional[float] = None
    annulus_p: Optional[float] = None
    pump_strokes: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    operator_id: Optional[str] = None
    manager_id: Optional[str] = None


# ── Reports ───────────────────────────────────────────────────────────────────

class ReportOut(BaseModel):
    id: str
    well_id: str
    well_code: Optional[str] = None
    well_name: Optional[str] = None
    operator_id: str
    operator_name: Optional[str] = None
    status: str
    ai_score: int
    summary: str
    flag: Optional[str] = None
    temperature: Optional[float] = None
    production24h: Optional[float] = None
    tubing_internal_p: Optional[float] = None
    tubing_external_p: Optional[float] = None
    annulus_p: Optional[float] = None
    pump_strokes: Optional[int] = None
    comment: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportCreate(BaseModel):
    well_id: str
    temperature: Optional[float] = None
    production24h: Optional[float] = None
    tubing_internal_p: Optional[float] = None
    tubing_external_p: Optional[float] = None
    annulus_p: Optional[float] = None
    pump_strokes: Optional[int] = None
    comment: Optional[str] = None


class ReportReview(BaseModel):
    status: str  # "approved" | "rejected"
    comment: Optional[str] = None


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: str
    icon: str
    title: str
    body: str
    tone: str
    unread: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Calendar Events ───────────────────────────────────────────────────────────

class CalendarEventOut(BaseModel):
    id: str
    title: str
    date: datetime
    event_type: str
    created_by: Optional[str] = None

    model_config = {"from_attributes": True}


class CalendarEventCreate(BaseModel):
    title: str
    date: datetime
    event_type: str = "Событие"


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: str
    who: str
    action: str
    target: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    active_wells: int
    warning_wells: int
    pending_reports: int
    flagged_reports: int
    total_production: float
    production_trend: list[dict]
    well_statuses: list[dict]


# ── AI ────────────────────────────────────────────────────────────────────────

class AIChatRequest(BaseModel):
    message: str


class AIChatResponse(BaseModel):
    reply: str
    suggestions: list[str] = []


# ── Production Trend ──────────────────────────────────────────────────────────

class ProductionTrendPoint(BaseModel):
    day: str
    oil: float
    gas: float


TokenResponse.model_rebuild()
