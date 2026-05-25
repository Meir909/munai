from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class RoleEnum(str, enum.Enum):
    operator = "operator"
    manager = "manager"
    director = "director"
    admin = "admin"


class WellStatusEnum(str, enum.Enum):
    active = "active"
    warning = "warning"
    inactive = "inactive"
    broken = "broken"


class ProductEnum(str, enum.Enum):
    oil = "oil"
    gas = "gas"
    condensate = "condensate"


class ReportStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    flagged = "flagged"
    rejected = "rejected"


class NotificationToneEnum(str, enum.Enum):
    warning = "warning"
    success = "success"
    info = "info"
    destructive = "destructive"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.operator)
    position = Column(String, default="")
    region = Column(String, default="")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship("Report", back_populates="user", foreign_keys="Report.operator_id")
    notifications = relationship("Notification", back_populates="user")


class Well(Base):
    __tablename__ = "wells"

    id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    status = Column(Enum(WellStatusEnum), default=WellStatusEnum.active)
    product = Column(Enum(ProductEnum), default=ProductEnum.oil)
    production24h = Column(Float, default=0.0)
    temperature = Column(Float, default=0.0)
    tubing_internal_p = Column(Float, default=0.0)
    tubing_external_p = Column(Float, default=0.0)
    annulus_p = Column(Float, default=0.0)
    pump_strokes = Column(Integer, default=0)
    lat = Column(Float, default=50.0)
    lng = Column(Float, default=55.0)
    operator_id = Column(String, ForeignKey("users.id"), nullable=True)
    manager_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    operator = relationship("User", foreign_keys=[operator_id])
    manager = relationship("User", foreign_keys=[manager_id])
    reports = relationship("Report", back_populates="well")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True)
    well_id = Column(String, ForeignKey("wells.id"), nullable=False)
    operator_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ReportStatusEnum), default=ReportStatusEnum.pending)
    ai_score = Column(Integer, default=0)
    summary = Column(Text, default="")
    flag = Column(String, nullable=True)
    temperature = Column(Float, nullable=True)
    production24h = Column(Float, nullable=True)
    tubing_internal_p = Column(Float, nullable=True)
    tubing_external_p = Column(Float, nullable=True)
    annulus_p = Column(Float, nullable=True)
    pump_strokes = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String, ForeignKey("users.id"), nullable=True)

    well = relationship("Well", back_populates="reports")
    user = relationship("User", back_populates="reports", foreign_keys=[operator_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    icon = Column(String, default="info")
    title = Column(String, nullable=False)
    body = Column(Text, default="")
    tone = Column(Enum(NotificationToneEnum), default=NotificationToneEnum.info)
    unread = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    event_type = Column(String, default="Событие")
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    who = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
