from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine, Base, SessionLocal
from routers import leads, agents, dashboard
from models import Agent, Lead
import random

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kayla Mahoney Realty Lead Command System")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(leads.router)
app.include_router(agents.router)
app.include_router(dashboard.router)

@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    if db.query(Agent).count() == 0:
        agents_data = [
            {"name": "Sarah Mitchell", "specialty": "Buyers $1M+"},
            {"name": "James Rodriguez", "specialty": "Buyers <$1M"},
            {"name": "Diana Chen", "specialty": "Sellers"},
            {"name": "Marcus Thompson", "specialty": "Generalist/Overflow"}
        ]
        for a in agents_data:
            db.add(Agent(**a))
        db.commit()
        
        # Seed Mock Leads — realistic luxury buyer/seller names
        agents_list = db.query(Agent).all()
        mock_leads = [
            {"name": "James Whitfield", "type": "buyer", "budget": "$2M+", "timeline": "ASAP"},
            {"name": "Sophia Reeves", "type": "seller", "budget": "$1.4M", "timeline": "1–3 months"},
            {"name": "Marcus Klein", "type": "buyer", "budget": "$1M–$2M", "timeline": "3–6 months"},
            {"name": "Elena Caruso", "type": "seller", "budget": "$2.2M", "timeline": "ASAP"},
            {"name": "Daniel Park", "type": "buyer", "budget": "$500K–$1M", "timeline": "1–3 months"},
            {"name": "Victoria Nash", "type": "buyer", "budget": "$2M+", "timeline": "ASAP"},
            {"name": "Ryan Holloway", "type": "seller", "budget": "$1.8M", "timeline": "3–6 months"},
            {"name": "Claire Fontaine", "type": "buyer", "budget": "$1M–$2M", "timeline": "1–3 months"},
        ]

        for data in mock_leads:
            chosen_agent = random.choice(agents_list)
            status = random.choice(["New", "Contacted"])
            lead = Lead(
                name=data["name"],
                email=f"{data['name'].lower().replace(' ', '.')}@example.com",
                phone="555-0100",
                lead_type=data["type"],
                budget_or_value=data["budget"],
                timeline=data["timeline"],
                assigned_agent_id=chosen_agent.id,
                status=status
            )
            db.add(lead)
            chosen_agent.leads_assigned += 1
            if status == "Contacted":
                chosen_agent.leads_responded += 1
        db.commit()
    db.close()

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")

@app.get("/dashboard")
def serve_dashboard():
    return FileResponse("static/dashboard.html")