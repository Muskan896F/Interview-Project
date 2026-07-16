from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class LeadResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    source: str
    status: str

class StartConversationResponse(BaseModel):
    session_id: str
    agent_text: str
    agent_audio_base64: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    user_text: Optional[str] = None        # transcribed customer speech
    agent_text: str
    agent_audio_base64: Optional[str] = None
    current_node: str
    language: str

class BookingResponse(BaseModel):
    status: str
    message: str

class SummaryResponse(BaseModel):
    session_id: str
    lead_id: int
    lead_score: int
    interested: Optional[bool] = None
    budget: Optional[str] = None
    preferred_location: Optional[str] = None
    property_type: Optional[str] = None
    purpose: Optional[str] = None
    timeline: Optional[str] = None
    questions_asked: List[str] = []
    objections: List[str] = []
    booking_status: Optional[str] = None
    follow_up_status: Optional[str] = None
    summary_text: Optional[str] = None
