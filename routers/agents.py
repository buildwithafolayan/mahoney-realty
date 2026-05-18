from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Agent

router = APIRouter(prefix="/api/agents", tags=["Agents"])

@router.get("")
def get_agents(db: Session = Depends(get_db)):
    agents = db.query(Agent).all()
    results = []
    for a in agents:
        avg_resp = "1m" if a.leads_responded > 0 else "N/A"
        results.append({
            "id": a.id,
            "name": a.name,
            "leads_assigned": a.leads_assigned,
            "leads_responded": a.leads_responded,
            "average_response_time": avg_resp,
            "status": "Available" if a.is_available else "Busy"
        })
    return results