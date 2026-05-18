from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Agent, Lead

router = APIRouter(prefix="/api/agents", tags=["Agents"])

@router.get("")
def get_agents(db: Session = Depends(get_db)):
    agents = db.query(Agent).all()
    results = []
    for a in agents:
        responded_leads = db.query(Lead).filter(
            Lead.assigned_agent_id == a.id,
            Lead.responded_at != None,
            Lead.created_at != None
        ).all()

        if responded_leads:
            total_seconds = int(sum(
                (lead.responded_at - lead.created_at).total_seconds()
                for lead in responded_leads
            ) / len(responded_leads))
            avg_resp = f"{total_seconds}s" if total_seconds < 60 else f"{total_seconds // 60}m {total_seconds % 60}s"
        else:
            avg_resp = "N/A"

        results.append({
            "id": a.id,
            "name": a.name,
            "leads_assigned": a.leads_assigned,
            "leads_responded": a.leads_responded,
            "average_response_time": avg_resp,
            "status": "Available" if a.is_available else "Busy"
        })
    return results