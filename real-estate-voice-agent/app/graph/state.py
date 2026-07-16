from typing import TypedDict, List, Dict, Any, Annotated
import operator

class ConversationState(TypedDict):
    """
    State object passed between LangGraph nodes.
    Maintains lead fields, dialog history, and current node indicators.
    """
    # Lead identity
    lead_name: str
    phone: str
    language: str
    db_lead_id: int
    
    # Dialog logs
    messages: Annotated[List[Dict[str, str]], operator.add]
    last_message: str
    agent_response: str
    
    # Qualification metrics
    budget: str
    preferred_location: str
    property_type: str
    purpose: str
    timeline: str
    
    # Booking metrics
    interested: bool
    booking_status: str  # "booked" | "follow_up" | "not_scheduled"
    booking_date: str
    booking_time: str
    followup_date: str
    followup_time: str
    
    # Operations
    objection_count: int
    current_node: str
    summary: Dict[str, Any]
