from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sqlfunc
from database import get_db
from models import Lead, Agent
from datetime import datetime, timedelta

router = APIRouter(prefix="/api", tags=["Dashboard"])

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    # Bug 1 fix: filter leads by today's date only
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total_leads = db.query(Lead).filter(Lead.created_at >= today_start).count()
    responded_leads = db.query(Lead).filter(Lead.status != "New", Lead.created_at >= today_start).count()
    pending = total_leads - responded_leads
    conv_rate = f"{(responded_leads / total_leads * 100):.1f}%" if total_leads > 0 else "0%"

    # Bug 2 fix: calculate average response time from real data
    responded = db.query(Lead).filter(
        Lead.responded_at != None,
        Lead.created_at != None
    ).all()

    if responded:
        total_secs = sum(
            (l.responded_at - l.created_at).total_seconds()
            for l in responded if l.responded_at and l.created_at
        )
        avg_secs = int(total_secs / len(responded))
        avg_display = f"{avg_secs}s" if avg_secs < 60 else f"{avg_secs // 60}m {avg_secs % 60}s"
    else:
        avg_display = "N/A"

    return {
        "total_leads_today": total_leads,
        "average_response_time": avg_display,
        "leads_pending": pending,
        "conversion_rate": conv_rate
    }

@router.get("/leads")
def get_all_leads(db: Session = Depends(get_db)):
    # Issue 1 fix: use joinedload to avoid N+1 queries
    leads = db.query(Lead).options(joinedload(Lead.agent)).order_by(Lead.created_at.desc()).all()
    result = []
    for lead in leads:
        result.append({
            "id": lead.id,
            "name": lead.name,
            "type": lead.lead_type.capitalize(),
            "contact": f"{lead.phone} | {lead.email}",
            "budget_or_value": lead.budget_or_value,
            "assigned_agent": lead.agent.name if lead.agent else "Unassigned",
            "created_at": (lead.created_at.isoformat() + "Z") if lead.created_at else None,
            "status": lead.status
        })
    return result

@router.get("/daily-stats")
def get_daily_stats(db: Session = Depends(get_db)):
    """Return lead count per day for the last 7 days."""
    today = datetime.utcnow().date()
    stats = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        count = db.query(Lead).filter(
            Lead.created_at >= day_start,
            Lead.created_at <= day_end
        ).count()
        stats.append({
            "date": day.strftime("%b %d"),
            "count": count
        })
    return stats