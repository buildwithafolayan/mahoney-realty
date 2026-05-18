from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    specialty = Column(String)
    leads_assigned = Column(Integer, default=0)
    leads_responded = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    lead_type = Column(String) # "buyer" or "seller"
    budget_or_value = Column(String)
    timeline = Column(String)
    message = Column(String, nullable=True)
    assigned_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    agent = relationship("Agent", foreign_keys=[assigned_agent_id])
    status = Column(String, default="New") # New, Contacted, Qualified, Closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True), nullable=True)
    response_scheduled_at = Column(DateTime(timezone=True), nullable=True)

class RoutingLog(Base):
    __tablename__ = "routing_logs"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    agent_id = Column(Integer, ForeignKey("agents.id"))
    routing_reason = Column(String)
    routed_at = Column(DateTime(timezone=True), server_default=func.now())