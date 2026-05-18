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
        
        # Seed Mock Leads — Bug 5 fix: increment agent counters
        agents_list = db.query(Agent).all()
        for i in range(8):
            l_type = random.choice(["buyer", "seller"])
            chosen_agent = random.choice(agents_list)
            status = random.choice(["New", "Contacted"])
            lead = Lead(
                name=f"Lead {i+1}",
                email=f"test{i}@example.com",
                phone="555-0100",
                lead_type=l_type,
                budget_or_value="$1M–$2M" if l_type == "buyer" else "$850K",
                timeline="1-3 months",
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