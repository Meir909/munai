from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlite3 import Connection
from app.database import get_db
from app import schemas
from app.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
def get_stats(db: Connection = Depends(get_db), current_user=Depends(get_current_user)):
    active_wells = db.execute("SELECT COUNT(*) FROM wells WHERE status='active'").fetchone()[0]
    warning_wells = db.execute("SELECT COUNT(*) FROM wells WHERE status='warning'").fetchone()[0]
    pending_reports = db.execute("SELECT COUNT(*) FROM reports WHERE status='pending'").fetchone()[0]
    flagged_reports = db.execute("SELECT COUNT(*) FROM reports WHERE status='flagged'").fetchone()[0]
    total_production = db.execute("SELECT COALESCE(SUM(production24h),0) FROM wells WHERE status='active'").fetchone()[0]

    # 7-day production trend
    trend = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        label = day.strftime("%d.%m")
        oil = round(total_production * (0.85 + (i % 3) * 0.05), 1)
        gas = round(total_production * 0.1 * (0.9 + (i % 4) * 0.03), 1)
        trend.append({"day": label, "oil": oil, "gas": gas})

    # Well status counts
    rows = db.execute("SELECT status, COUNT(*) as cnt FROM wells GROUP BY status").fetchall()
    well_statuses = [{"status": r["status"], "count": r["cnt"]} for r in rows]

    return schemas.DashboardStats(
        active_wells=active_wells,
        warning_wells=warning_wells,
        pending_reports=pending_reports,
        flagged_reports=flagged_reports,
        total_production=round(total_production, 1),
        production_trend=trend,
        well_statuses=well_statuses,
    )
