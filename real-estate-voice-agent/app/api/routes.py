from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import database, crud, schema
from app.api.request_models import (
    CreateLeadRequest, StartConversationRequest, ChatRequest,
    BookVisitRequest, FollowUpRequest
)
from app.api.response_models import (
    LeadResponse, StartConversationResponse, ChatResponse,
    BookingResponse, SummaryResponse
)
from app.graph.graph import agent_workflow
from app.config import constants
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service
from app.services.memory_service import memory_service
from app.services.summary_service import summary_service
from app.utils.helpers import generate_session_id
from app.utils.validators import validate_phone
from app.utils.logger import logger
from app.services.export_service import export_conversations, export_summaries

router = APIRouter()

def language_to_tts_code(language: str) -> str:
    """Maps conversation language name to Sarvam TTS language code."""
    mapping = {
        "hindi": "hi-IN",
        "english": "en-IN",
        "gujarati": "gu-IN",
    }
    return mapping.get(language.lower(), "gu-IN")

@router.post("/create-lead", response_model=LeadResponse)
def create_lead_endpoint(req: CreateLeadRequest, db: Session = Depends(database.get_db)):
    """Inserts a new prospective buyer lead record into the database."""
    if not validate_phone(req.phone):
        raise HTTPException(status_code=400, detail="Invalid Indian mobile number format.")
    
    existing = crud.get_lead_by_phone(db, req.phone)
    if existing:
        return existing
        
    lead_create = schema.LeadCreate(
        name=req.name,
        phone=req.phone,
        email=req.email,
        source=req.source
    )
    return crud.create_lead(db, lead_create)

@router.post("/start-conversation", response_model=StartConversationResponse)
def start_conversation_endpoint(req: StartConversationRequest, db: Session = Depends(database.get_db)):
    """Initiates an outbound voice call session, invoking the Greeting Node."""
    lead = crud.get_lead_by_phone(db, req.phone)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found. Register lead first.")

    session_id = generate_session_id()
    
    # Initialize blank conversation state
    initial_state = {
        "lead_name": lead.name,
        "phone": lead.phone,
        "language": constants.DEFAULT_LANGUAGE,
        "db_lead_id": lead.id,
        "messages": [],
        "last_message": "",
        "agent_response": "",
        "budget": "",
        "preferred_location": "",
        "property_type": "",
        "purpose": "",
        "timeline": "",
        "interested": False,
        "booking_status": "not_scheduled",
        "booking_date": "",
        "booking_time": "",
        "followup_date": "",
        "followup_time": "",
        "objection_count": 0,
        "current_node": constants.Node.GREETING,
        "summary": {}
    }

    # Run LangGraph Greeting node
    try:
        output_state = agent_workflow.invoke(initial_state)
    except Exception as e:
        logger.error(f"LangGraph execution error during greeting: {e}")
        raise HTTPException(status_code=500, detail="Graph workflow initialization failed.")

    agent_text = output_state.get("agent_response", "Hello")
    
    # Save the updated state to memory
    memory_service.save_conversation_state(session_id, lead.id, output_state, db)
    
    # Synthesize Greeting Audio — use detected language for TTS
    tts_lang = language_to_tts_code(output_state.get("language", "gujarati"))
    audio_base64 = tts_service.text_to_speech(agent_text, tts_lang)
    
    # Export conversations snapshot after session is created
    export_conversations(db)

    return StartConversationResponse(
        session_id=session_id,
        agent_text=agent_text,
        agent_audio_base64=audio_base64
    )

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, db: Session = Depends(database.get_db)):
    """Processes conversational turns, transcribing voice, stepping nodes, and updating databases."""
    conv = crud.get_conversation(db, req.session_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation session not found.")

    # Retrieve existing state dictionary first to know language
    state = memory_service.load_conversation_state(req.session_id, db)

    # 1. Decode speech audio if provided
    user_text = req.user_text or ""
    if req.user_audio_base64:
        user_text = stt_service.transcribe_base64(req.user_audio_base64)

    if not user_text:
        # Instead of 400 Bad Request error, return a friendly prompt asking to repeat in the current language
        lang = state.get("language", "gujarati").lower()
        if "hi" in lang:
            agent_text = "Mujhe aapki aawaz nahi aayi. Kya aap please repeat karenge?"
            tts_lang = "hi-IN"
        elif "en" in lang:
            agent_text = "I couldn't hear you clearly. Could you please repeat that?"
            tts_lang = "en-IN"
        else:
            agent_text = "Sorry, mane tamari aavaj barobar na aavi. Tame e jara repeat karso?"
            tts_lang = "gu-IN"
            
        audio_base64 = tts_service.text_to_speech(agent_text, tts_lang)
        return ChatResponse(
            session_id=req.session_id,
            agent_text=agent_text,
            agent_audio_base64=audio_base64,
            current_node=state.get("current_node", "qualification"),
            language=state.get("language", "gujarati")
        )

    # Update input logs in state
    state["last_message"] = user_text
    state["messages"].append({"role": "user", "content": user_text})
    
    try:
        # Step through the workflow turn
        output_state = agent_workflow.invoke(state)
    except Exception as e:

        logger.error(f"Graph execution failed: {e}")
        raise HTTPException(status_code=500, detail="Graph failed to route next turn.")

    agent_text = output_state.get("agent_response", "")
    current_phase = output_state.get("current_node", "end")

    # 3. Handle intermediate node saves & updates
    # Update lead qualification parameters inside DB when collected
    lead_id = state.get("db_lead_id")
    for field in constants.QUALIFICATION_FIELDS:
        if output_state.get(field):
            # Write key updates back
            pass
            
    # Check if a booking was confirmed in node transitions
    if current_phase == constants.Node.BOOKING and output_state.get("booking_date") and output_state.get("booking_time"):
        memory_service.save_booking(
            lead_id, req.session_id, "site_visit", 
            output_state.get("booking_date"), output_state.get("booking_time"), db
        )
    elif current_phase == constants.Node.FOLLOWUP and output_state.get("followup_date") and output_state.get("followup_time"):
        memory_service.save_booking(
            lead_id, req.session_id, "follow_up", 
            output_state.get("followup_date"), output_state.get("followup_time"), db
        )

    # Save final conversation state dictionary back to DB
    memory_service.save_conversation_state(req.session_id, lead_id, output_state, db)

    # If conversation concluded or reached summary phase, compile lead analytics
    if current_phase == constants.Node.SUMMARY or current_phase == constants.Node.END:
        summary_data = output_state.get("summary", {})
        if summary_data:
            memory_service.save_summary(req.session_id, lead_id, summary_data, db)
            crud.end_conversation(db, req.session_id)

    # 4. Convert output text to voice — use correct language for TTS
    tts_lang = language_to_tts_code(output_state.get("language", "gujarati"))
    audio_base64 = tts_service.text_to_speech(agent_text, tts_lang)

    # 5. Export updated conversation transcript to JSON after every turn
    export_conversations(db)

    # Export summaries JSON when call reaches summary/end node
    if current_phase in (constants.Node.SUMMARY, constants.Node.END):
        export_summaries(db)

    return ChatResponse(
        session_id=req.session_id,
        user_text=user_text,
        agent_text=agent_text,
        agent_audio_base64=audio_base64,
        current_node=current_phase,
        language=output_state.get("language", "gujarati")
    )

@router.post("/book-visit", response_model=BookingResponse)
def book_visit_endpoint(req: BookVisitRequest, db: Session = Depends(database.get_db)):
    """API endpoint to directly register a site visit booking."""
    conv = crud.get_conversation(db, req.session_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    memory_service.save_booking(conv.lead_id, req.session_id, "site_visit", req.date, req.time, db)
    return BookingResponse(status="success", message="Site visit booking confirmed successfully.")

@router.post("/follow-up", response_model=BookingResponse)
def follow_up_endpoint(req: FollowUpRequest, db: Session = Depends(database.get_db)):
    """API endpoint to directly register a callback follow-up."""
    conv = crud.get_conversation(db, req.session_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    memory_service.save_booking(conv.lead_id, req.session_id, "follow_up", req.date, req.time, db)
    return BookingResponse(status="success", message="Callback follow-up scheduled successfully.")

@router.get("/summary", response_model=SummaryResponse)
def get_summary_endpoint(session_id: str = Query(..., description="The session ID to fetch summary details for"), db: Session = Depends(database.get_db)):
    """Fetches lead qualification summaries and dialogue insights."""
    summary = crud.get_summary(db, session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary logs not found for this session.")
        
    return SummaryResponse(
        session_id=summary.session_id,
        lead_id=summary.lead_id,
        lead_score=summary.lead_score,
        interested=summary.interested,
        budget=summary.budget,
        preferred_location=summary.preferred_location,
        property_type=summary.property_type,
        purpose=summary.purpose,
        timeline=summary.timeline,
        questions_asked=summary.questions_asked or [],
        objections=summary.objections or [],
        booking_status=summary.booking_status,
        follow_up_status=summary.follow_up_status,
        summary_text=summary.summary_text
    )
