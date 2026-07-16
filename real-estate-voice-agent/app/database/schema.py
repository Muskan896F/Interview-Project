"""
Pydantic schemas for API request/response validation and DB serialization.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Lead Schemas ──
class LeadCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    source: Optional[str] = "web_form"


class LeadOut(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    source: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Conversation Schemas ──
class ConversationOut(BaseModel):
    id: int
    session_id: str
    lead_id: int
    language: str
    current_node: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Booking Schemas ──
class BookingCreate(BaseModel):
    lead_id: int
    session_id: str
    booking_type: str  # site_visit | follow_up
    date: Optional[str] = None
    time: Optional[str] = None


class BookingOut(BaseModel):
    id: int
    lead_id: int
    session_id: str
    booking_type: str
    date: Optional[str] = None
    time: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Summary Schemas ──
class SummaryCreate(BaseModel):
    session_id: str
    lead_id: int
    lead_score: int = 0
    interested: Optional[bool] = None
    budget: Optional[str] = None
    preferred_location: Optional[str] = None
    property_type: Optional[str] = None
    purpose: Optional[str] = None
    timeline: Optional[str] = None
    questions_asked: Optional[List[str]] = None
    objections: Optional[List[str]] = None
    booking_status: Optional[str] = None
    follow_up_status: Optional[str] = None
    summary_text: Optional[str] = None


class SummaryOut(BaseModel):
    id: int
    session_id: str
    lead_id: int
    lead_score: int
    interested: Optional[bool] = None
    budget: Optional[str] = None
    preferred_location: Optional[str] = None
    property_type: Optional[str] = None
    purpose: Optional[str] = None
    timeline: Optional[str] = None
    questions_asked: Optional[List[str]] = None
    objections: Optional[List[str]] = None
    booking_status: Optional[str] = None
    follow_up_status: Optional[str] = None
    summary_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
