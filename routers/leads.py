from fastapi import APIRouter, Depends, Form, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models import Lead, Agent, RoutingLog
from datetime import datetime, timedelta
import random

router = APIRouter(tags=["Leads"])

def route_lead(db: Session, lead: Lead):
    # Retrieve mock agents
    sarah = db.query(Agent).filter(Agent.name == "Sarah Mitchell").first()
    james = db.query(Agent).filter(Agent.name == "James Rodriguez").first()
    diana = db.query(Agent).filter(Agent.name == "Diana Chen").first()
    marcus = db.query(Agent).filter(Agent.name == "Marcus Thompson").first()

    # Bug 4 fix: guard against missing agents
    if not all([sarah, james, diana, marcus]):
        print("ERROR: Agent(s) missing from DB — cannot route lead.")
        return

    assigned_agent = None
    reason = ""

    if lead.lead_type == "seller":
        if diana.leads_assigned - diana.leads_responded >= 5:
            assigned_agent = marcus
            reason = "Diana overflow -> Marcus"
        else:
            assigned_agent = diana
            reason = "Specialty: Seller"
    else:
        if lead.budget_or_value == "$2M+" or lead.budget_or_value == "$1M–$2M":
            if sarah.leads_assigned - sarah.leads_responded >= 5:
                assigned_agent = marcus
                reason = "Sarah overflow -> Marcus"
            else:
                assigned_agent = sarah
                reason = "Specialty: Buyer > $1M"
        else:
            if james.leads_assigned - james.leads_responded >= 5:
                assigned_agent = marcus
                reason = "James overflow -> Marcus"
            else:
                assigned_agent = james
                reason = "Specialty: Buyer < $1M"

    lead.assigned_agent_id = assigned_agent.id
    lead.response_scheduled_at = datetime.utcnow() + timedelta(seconds=60)
    assigned_agent.leads_assigned += 1
    
    log = RoutingLog(lead_id=lead.id, agent_id=assigned_agent.id, routing_reason=reason)
    db.add(log)
    db.commit()
    print(f"SYSTEM ACTION: Routed {lead.name} to {assigned_agent.name} via '{reason}'. Response locked for 60s.")

# Bug 3 fix: background tasks get their own DB session
def route_lead_task(lead_id: int):
    """Opens its own session — safe in background tasks."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            route_lead(db, lead)
    finally:
        db.close()

@router.post("/leads/buyer")
def capture_buyer(
    background_tasks: BackgroundTasks,
    name: str = Form(...), email: str = Form(...), phone: str = Form(...),
    budget: str = Form(...), timeline: str = Form(...), message: str = Form(""),
    db: Session = Depends(get_db)
):
    new_lead = Lead(name=name, email=email, phone=phone, lead_type="buyer", budget_or_value=budget, timeline=timeline, message=message)
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    background_tasks.add_task(route_lead_task, new_lead.id)
    return {"message": "Our team will contact you within 60 seconds."}

@router.post("/leads/seller")
def capture_seller(
    background_tasks: BackgroundTasks,
    name: str = Form(...), email: str = Form(...), phone: str = Form(...),
    address: str = Form(...), value: str = Form(...), timeline: str = Form(...),
    db: Session = Depends(get_db)
):
    new_lead = Lead(name=name, email=email, phone=phone, lead_type="seller", budget_or_value=value, timeline=timeline, message=f"Address: {address}")
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    background_tasks.add_task(route_lead_task, new_lead.id)
    return {"message": "Our team will contact you within 60 seconds."}

@router.post("/simulate/new-lead")
def simulate_lead(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    is_buyer = random.choice([True, False])
    names = ["Alexander Pierce", "Eleanor Vance", "Liam Sterling", "Sophia Rossi"]
    budgets = ["$500K–$1M", "$1M–$2M", "$2M+"]
    
    new_lead = Lead(
        name=random.choice(names),
        email=f"client_{random.randint(100,999)}@example.com",
        phone=f"555-01{random.randint(10,99)}",
        lead_type="buyer" if is_buyer else "seller",
        budget_or_value=random.choice(budgets),
        timeline="ASAP"
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    route_lead(db, new_lead)
    agent = db.query(Agent).filter(Agent.id == new_lead.assigned_agent_id).first()
    return {
        "status": "Simulated lead injected",
        "lead_name": new_lead.name,
        "assigned_agent": agent.name if agent else "Unassigned"
    }

@router.post("/leads/{lead_id}/contacted")
def mark_contacted(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if lead and lead.status == "New":
        lead.status = "Contacted"
        lead.responded_at = datetime.utcnow()
        agent = db.query(Agent).filter(Agent.id == lead.assigned_agent_id).first()
        if agent:
            agent.leads_responded += 1
        db.commit()
    return {"status": "success"}