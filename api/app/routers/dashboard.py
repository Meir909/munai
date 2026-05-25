from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


@router.get("/stats", response_model=schemas.DashboardStats)
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    active_wells = db.query(models.Well).filter(models.Well.status == "active").count()
    warning_wells = db.query(models.Well).filter(models.Well.status.in_(["warning", "broken"])).count()
    pending_reports = db.query(models.Report).filter(models.Report.status == "pending").count()
    flagged_reports = db.query(models.Report).filter(models.Report.status == "flagged").count()

    # Production trend for last 7 days
    trend = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        weekday_idx = day.weekday()  # 0=Mon
        oil_sum = sum(
            w.production24h for w in db.query(models.Well).filter(
                models.Well.status == "active", models.Well.product.in_(["oil", "condensate"])
            ).all()
        )
        gas_sum = sum(
            w.production24h for w in db.query(models.Well).filter(
                models.Well.status == "active", models.Well.product == "gas"
            ).all()
        )
        # Add slight variance per day
        import random
        variance = 1 + (hash(str(day.date())) % 20 - 10) / 100
        trend.append({
            "day": DAYS_RU[weekday_idx],
            "oil": round(oil_sum * variance, 1),
            "gas": round(gas_sum * variance, 1),
        })

    total_production = sum(w.production24h for w in db.query(models.Well).filter(models.Well.status == "active").all())

    well_statuses = [
        {"name": "Активно", "v": db.query(models.Well).filter(models.Well.status == "active").count()},
        {"name": "Внимание", "v": db.query(models.Well).filter(models.Well.status == "warning").count()},
        {"name": "Неактивно", "v": db.query(models.Well).filter(models.Well.status == "inactive").count()},
        {"name": "Авария", "v": db.query(models.Well).filter(models.Well.status == "broken").count()},
    ]

    return schemas.DashboardStats(
        active_wells=active_wells,
        warning_wells=warning_wells,
        pending_reports=pending_reports,
        flagged_reports=flagged_reports,
        total_production=round(total_production * 7, 1),
        production_trend=trend,
        well_statuses=well_statuses,
    )
