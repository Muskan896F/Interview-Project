"""
Shared Pydantic models and type aliases used across layers.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class Message(BaseModel):
    """Single chat turn stored in conversation history."""
    role: str  # "user" | "assistant" | "system"
    content: str


class LeadInfo(BaseModel):
    """Lightweight lead snapshot passed between services."""
    name: str
    phone: str
    email: Optional[str] = None
    source: Optional[str] = "web_form"


class ConversationTurn(BaseModel):
    """One request-response turn exchanged with the frontend."""
    session_id: str
    user_text: Optional[str] = None
    user_audio_base64: Optional[str] = None
    agent_text: Optional[str] = None
    agent_audio_base64: Optional[str] = None
    current_node: Optional[str] = None
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
