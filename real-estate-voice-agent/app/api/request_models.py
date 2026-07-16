from pydantic import BaseModel, Field
from typing import Optional

class CreateLeadRequest(BaseModel):
    name: str = Field(..., description="Name of the prospective lead")
    phone: str = Field(..., description="10-digit mobile contact number")
    email: Optional[str] = Field(None, description="Email address (optional)")
    source: Optional[str] = Field("web_form", description="Origin of lead, e.g. web ad")

class StartConversationRequest(BaseModel):
    phone: str = Field(..., description="Phone number associated with the registered lead")

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Active session ID key")
    user_text: Optional[str] = Field(None, description="Typed text message from user")
    user_audio_base64: Optional[str] = Field(None, description="Base64 encoded speech audio wav string")

class BookVisitRequest(BaseModel):
    session_id: str = Field(..., description="Active session ID key")
    date: str = Field(..., description="Preferred site visit date, e.g. Saturday")
    time: str = Field(..., description="Preferred site visit timing, e.g. 11 AM")

class FollowUpRequest(BaseModel):
    session_id: str = Field(..., description="Active session ID key")
    date: str = Field(..., description="Preferred callback date")
    time: str = Field(..., description="Preferred callback timing")
