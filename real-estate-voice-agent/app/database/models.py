"""
SQLAlchemy ORM models — Lead, Conversation, Booking, Summary.
"""

import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship
from app.database.database import Base


class Lead(Base):
    """Prospective buyer generated from a web-form / ad click."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, nullable=True)
    source = Column(String, default="web_form")
    status = Column(String, default="new")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    conversations = relationship("Conversation", back_populates="lead")
    bookings = relationship("Booking", back_populates="lead")
    summaries = relationship("Summary", back_populates="lead")


class Conversation(Base):
    """Stores the full LangGraph state as JSON for resumability."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    language = Column(String, default="gujarati")
    current_node = Column(String, default="greeting")
    state_json = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    lead = relationship("Lead", back_populates="conversations")


class Booking(Base):
    """Site-visit or follow-up booking linked to a lead."""
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    session_id = Column(String, nullable=False)
    booking_type = Column(String, nullable=False)  # site_visit | follow_up
    date = Column(String, nullable=True)
    time = Column(String, nullable=True)
    status = Column(String, default="confirmed")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    lead = relationship("Lead", back_populates="bookings")


class Summary(Base):
    """AI-generated conversation summary with lead scoring."""
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, unique=True, nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    lead_score = Column(Integer, default=0)
    interested = Column(Boolean, nullable=True)
    budget = Column(String, nullable=True)
    preferred_location = Column(String, nullable=True)
    property_type = Column(String, nullable=True)
    purpose = Column(String, nullable=True)
    timeline = Column(String, nullable=True)
    questions_asked = Column(JSON, nullable=True)
    objections = Column(JSON, nullable=True)
    booking_status = Column(String, nullable=True)
    follow_up_status = Column(String, nullable=True)
    summary_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    lead = relationship("Lead", back_populates="summaries")
