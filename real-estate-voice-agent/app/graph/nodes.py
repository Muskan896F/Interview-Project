from typing import Dict, Any
from app.graph.state import ConversationState
from app.config import constants
from app.services.llm_service import llm_service
from app.services.prompt_builder import prompt_builder
from app.services.knowledge_service import knowledge_service
from app.services.summary_service import summary_service
from app.services.language_service import language_service
from app.utils.logger import logger


# ── STT Normalization helpers ──
_SPOKEN_BHK = {
    # Standard abbreviation variants
    "one bhk": "1 BHK", "one b hk": "1 BHK", "one b h k": "1 BHK", "1bhk": "1 BHK",
    "two bhk": "2 BHK", "two b hk": "2 BHK", "two b h k": "2 BHK", "2bhk": "2 BHK",
    "three bhk": "3 BHK", "three b hk": "3 BHK", "three b h k": "3 BHK", "3bhk": "3 BHK",
    "four bhk": "4 BHK", "four b hk": "4 BHK", "four b h k": "4 BHK", "4bhk": "4 BHK",
    "2 b hk": "2 BHK", "3 b hk": "3 BHK", "4 b hk": "4 BHK",
    "2 b h k": "2 BHK", "3 b h k": "3 BHK", "4 b h k": "4 BHK",
    # Full form "Bedroom Hall Kitchen" variants (user mimics TTS output)
    "one bedroom hall kitchen": "1 BHK", "1 bedroom hall kitchen": "1 BHK",
    "two bedroom hall kitchen": "2 BHK", "2 bedroom hall kitchen": "2 BHK",
    "three bedroom hall kitchen": "3 BHK", "3 bedroom hall kitchen": "3 BHK",
    "four bedroom hall kitchen": "4 BHK", "4 bedroom hall kitchen": "4 BHK",
    # Common STT misheard forms ("hall" → "all", "bed room" split, etc.)
    "one bedroom all kitchen": "1 BHK", "1 bedroom all kitchen": "1 BHK",
    "two bedroom all kitchen": "2 BHK", "2 bedroom all kitchen": "2 BHK",
    "three bedroom all kitchen": "3 BHK", "3 bedroom all kitchen": "3 BHK",
    "four bedroom all kitchen": "4 BHK", "4 bedroom all kitchen": "4 BHK",
    "one bed room hall kitchen": "1 BHK", "two bed room hall kitchen": "2 BHK",
    "three bed room hall kitchen": "3 BHK", "four bed room hall kitchen": "4 BHK",
    # Standalone "bedroom hall kitchen" without a number prefix
    "bedroom hall kitchen": "BHK", "bedroom all kitchen": "BHK",
    "bed room hall kitchen": "BHK",
}

def _normalize_stt(text: str) -> str:
    """Normalise common Deepgram STT transcription artifacts for qualification answers."""
    normalized = text.lower().strip()
    for spoken, standard in _SPOKEN_BHK.items():
        if spoken in normalized:
            normalized = normalized.replace(spoken, standard)
    return normalized


def greeting_node(state: ConversationState) -> Dict[str, Any]:
    """Greets the lead dynamically in Code-Mixed Gujarati."""
    logger.info("Executing Greeting Node")
    
    system_prompt = prompt_builder.build_prompt("system_prompt.txt")
    user_prompt = prompt_builder.build_prompt("greeting_prompt.txt", lead_name=state.get("lead_name", "Customer"))
    
    response = llm_service.generate(system_prompt, user_prompt)
    
    return {
        "current_node": constants.Node.GREETING,
        "agent_response": response,
        "messages": [{"role": "assistant", "content": response}]
    }

def permission_node(state: ConversationState) -> Dict[str, Any]:
    """Asks client for permission to begin qualification questions."""
    logger.info("Executing Permission Node")
    
    system_prompt = prompt_builder.build_prompt("system_prompt.txt")
    lang = state.get("language", "gujarati")
    last_msg = state.get("last_message", "").lower()

    # Check if the customer declined (said no / busy / not now)
    denial_words = ["no", "nahi", "na", "busy", "not now", "pachi", "later", "nathi", "abhi nahi", "nai"]
    is_denial = any(w in last_msg for w in denial_words)

    if is_denial:
        # Professional farewell — do not continue questioning
        farewell = (
            "Bilkul sir/ma'am, koi vaat nahi! Hu tamne baad mai call karis. Aapno din shubh rahe!"
            if lang == "gujarati" else
            "Bilkul, koi baat nahi! Main baad mein call karti hoon. Aapka din shubh rahe!"
            if lang == "hindi" else
            "Of course, no problem at all! I'll reach out at a more convenient time. Have a great day!"
        )
        response = llm_service.generate(
            system_prompt,
            f"The customer is not available right now. Say a warm, professional goodbye. Language: {lang}. Suggestion: '{farewell}'"
        )
        return {
            "current_node": constants.Node.END,
            "agent_response": response,
            "messages": [{"role": "assistant", "content": response}]
        }

    # Customer said yes — ask for permission to proceed with questions
    permission_query = (
        "Khub saras! Hu tamare mate best property option find kari shaku e mate shu hu tamne thoda questions puchhi shaku?"
        if lang == "gujarati" else
        "Bahut achha! Kya main aapse Shubh Residency ke baare mein kuch quick questions pooch sakti hoon?"
        if lang == "hindi" else
        "Wonderful! May I ask you a few quick questions to help find the perfect property configuration for you?"
    )
    
    response = llm_service.generate(
        system_prompt, 
        f"The customer confirmed they are available. Ask permission to proceed with qualification questions. Language: {lang}. Suggestion: '{permission_query}'"
    )
    
    return {
        "current_node": constants.Node.PERMISSION,
        "agent_response": response,
        "messages": [{"role": "assistant", "content": response}]
    }

def language_detection_node(state: ConversationState) -> Dict[str, Any]:
    """Evaluates user input language, runs extraction on incoming answer, and updates state."""
    logger.info("Executing Language Detection & Extraction Node")
    user_text = state.get("last_message", "")
    current_language = state.get("language", "gujarati")
    detected_lang = language_service.detect_language(user_text, current_language)
    
    updates = {
        "language": detected_lang
    }
    
    # Run global extraction on the last missing field so we capture it even on interrupts/objections/other turns
    if user_text:
        normalized_input = _normalize_stt(user_text)
        if normalized_input != user_text.lower().strip():
            logger.info(f"STT normalization: '{user_text}' → '{normalized_input}'")
        
        # 1. Check if we are in qualification phase
        qualification_missing = any(not state.get(f) for f in constants.QUALIFICATION_FIELDS)
        if qualification_missing:
            for field in constants.QUALIFICATION_FIELDS:
                if not state.get(field):
                    extract_prompt = prompt_builder.build_prompt(
                        "extract_prompt.txt",
                        field_name=field.replace("_", " "),
                        user_input=normalized_input
                    )
                    raw = llm_service.generate(
                        "You are a data extraction assistant. Extract exactly what was asked. Return only the value or NOT_FOUND.",
                        extract_prompt
                    ).strip()
                    
                    if raw and raw.upper() != "NOT_FOUND" and len(raw) < 80:
                        updates[field] = raw
                        logger.info(f"Global extraction captured: {field} = '{raw}'")
                    break
        
        # 2. Check if we are in booking phase
        elif state.get("current_node") == constants.Node.BOOKING:
            for field in ["booking_date", "booking_time"]:
                if not state.get(field):
                    extract_prompt = prompt_builder.build_prompt(
                        "extract_prompt.txt",
                        field_name=field.replace("_", " "),
                        user_input=normalized_input
                    )
                    raw = llm_service.generate(
                        "You are a data extraction assistant. Extract exactly what was asked. Return only the value or NOT_FOUND.",
                        extract_prompt
                    ).strip()
                    
                    if raw and raw.upper() != "NOT_FOUND" and len(raw) < 80:
                        updates[field] = raw
                        logger.info(f"Global booking extraction captured: {field} = '{raw}'")
        
        # 3. Check if we are in followup phase
        elif state.get("current_node") == constants.Node.FOLLOWUP:
            for field in ["followup_date", "followup_time"]:
                if not state.get(field):
                    extract_prompt = prompt_builder.build_prompt(
                        "extract_prompt.txt",
                        field_name=field.replace("_", " "),
                        user_input=normalized_input
                    )
                    raw = llm_service.generate(
                        "You are a data extraction assistant. Extract exactly what was asked. Return only the value or NOT_FOUND.",
                        extract_prompt
                    ).strip()
                    
                    if raw and raw.upper() != "NOT_FOUND" and len(raw) < 80:
                        updates[field] = raw
                        logger.info(f"Global followup extraction captured: {field} = '{raw}'")
                        
    return updates


def qualification_node(state: ConversationState) -> Dict[str, Any]:
    """Collects missing qualification fields one question at a time.
    
    Checks the next still-missing field and asks for it.
    """
    logger.info("Executing Qualification Node")
    
    # ── Step 1: Find the next still-missing field ──
    missing_field = None
    for field in constants.QUALIFICATION_FIELDS:
        if not state.get(field):
            missing_field = field
            break
            
    if not missing_field:
        # All qualified fields are present. Prompt for booking decision.
        logger.info("All qualification fields collected. Transitioning to booking decision.")
        booking_result = booking_decision_node(state)
        return booking_result

    # ── Step 2: Ask the next missing field ──
    lead_details_str = (
        f"Budget: {state.get('budget') or 'Not captured'}\n"
        f"Preferred Location: {state.get('preferred_location') or 'Not captured'}\n"
        f"Property Type: {state.get('property_type') or 'Not captured'}\n"
        f"Purpose: {state.get('purpose') or 'Not captured'}\n"
        f"Timeline: {state.get('timeline') or 'Not captured'}"
    )

    system_prompt = prompt_builder.build_prompt("system_prompt.txt")
    user_prompt = prompt_builder.build_prompt(
        "qualification_prompt.txt",
        lead_details=lead_details_str,
        next_field=missing_field.replace("_", " "),
        current_language=state.get("language", "gujarati")
    )
    
    response = llm_service.generate(system_prompt, user_prompt)
    
    return {
        "current_node": constants.Node.QUALIFICATION,
        "agent_response": response,
        "messages": [{"role": "assistant", "content": response}]
    }

def knowledge_node(state: ConversationState) -> Dict[str, Any]:
    """Answers specific client questions using JSON knowledge bases."""
    logger.info("Executing Knowledge Node")
    user_input = state.get("last_message", "")
    
    context = knowledge_service.get_combined_context(user_input)
    
    system_prompt = prompt_builder.build_prompt("system_prompt.txt")
    user_prompt = prompt_builder.build_prompt(
        "knowledge_prompt.txt",
        user_input=user_input,
        knowledge_context=context,
        current_language=state.get("language", "gujarati")
    )
    
    response = llm_service.generate(system_prompt, user_prompt)
    
    return {
        "current_node": constants.Node.KNOWLEDGE,
        "agent_response": response,
        "messages": [{"role": "assistant", "content": response}]
    }

def objection_node(state: ConversationState) -> Dict[str, Any]:
    """Handles objections (high price, busy, family discussion, etc.) politely."""
    logger.info("Executing Objection Node")
    user_input = state.get("last_message", "")
    
    system_prompt = prompt_builder.build_prompt("system_prompt.txt")
    user_prompt = prompt_builder.build_prompt(
        "objection_prompt.txt",
        user_input=user_input,
        current_language=state.get("language", "gujarati")
    )
    
    response = llm_service.generate(system_prompt, user_prompt)
    
    return {
        "current_node": constants.Node.OBJECTION,
        "agent_response": response,
        "objection_count": state.get("objection_count", 0) + 1,
        "messages": [{"role": "assistant", "content": response}]
    }

def booking_decision_node(state: ConversationState) -> Dict[str, Any]:
    """Asks client to commit to a site visit or callback."""
    logger.info("Executing Booking Decision Node")
    
    system_prompt = prompt_builder.build_prompt("system_prompt.txt")
    lang = state.get("language", "gujarati")
    
    decision_query = (
        "Saru, to tame aa weekend par project ni mulakat leva mate site visit schedule karva mango cho?"
        if lang == "gujarati" else
        "Theek hai, toh kya aap is weekend site visit schedule karna chahenge?"
        if lang == "hindi" else
        "Great, would you like to schedule a site visit this coming weekend to view our sample flats?"
    )
    
    response = llm_service.generate(
        system_prompt,
        f"The conversation is already ongoing. NEVER say 'Hello' or introduce yourself. Politely ask the user if they want to book a site visit. Language: {lang}. Suggestion: '{decision_query}'"
    )
    
    return {
        "current_node": constants.Node.BOOKING_DECISION,
        "agent_response": response,
        "messages": [{"role": "assistant", "content": response}]
    }

def booking_node(state: ConversationState) -> Dict[str, Any]:
    """Schedules preferred date and time for site visits."""
    logger.info("Executing Booking Node")
    
    system_prompt = prompt_builder.build_prompt("system_prompt.txt")
    user_prompt = prompt_builder.build_prompt(
        "booking_prompt.txt",
        booking_date=state.get("booking_date") or "Not scheduled",
        booking_time=state.get("booking_time") or "Not scheduled",
        current_language=state.get("language", "gujarati")
    )
    
    response = llm_service.generate(system_prompt, user_prompt)
    
    return {
        "current_node": constants.Node.BOOKING,
        "booking_status": "booked",
        "agent_response": response,
        "messages": [{"role": "assistant", "content": response}]
    }

def followup_node(state: ConversationState) -> Dict[str, Any]:
    """Schedules callback details when customer is not ready to visit."""
    logger.info("Executing Follow-up Node")
    
    system_prompt = prompt_builder.build_prompt("system_prompt.txt")
    user_prompt = prompt_builder.build_prompt(
        "followup_prompt.txt",
        followup_date=state.get("followup_date") or "Not scheduled",
        followup_time=state.get("followup_time") or "Not scheduled",
        current_language=state.get("language", "gujarati")
    )
    
    response = llm_service.generate(system_prompt, user_prompt)
    
    return {
        "current_node": constants.Node.FOLLOWUP,
        "booking_status": "follow_up",
        "agent_response": response,
        "messages": [{"role": "assistant", "content": response}]
    }

def summary_node(state: ConversationState) -> Dict[str, Any]:
    """Triggers dialogue summary compilation."""
    logger.info("Executing Summary Node")
    
    summary_data = summary_service.generate_summary(
        session_id="simulated-session",
        lead_name=state.get("lead_name", "Customer"),
        phone=state.get("phone", ""),
        state_data=state,
        messages_list=state.get("messages", [])
    )
    
    return {
        "current_node": constants.Node.SUMMARY,
        "summary": summary_data
    }

def end_node(state: ConversationState) -> Dict[str, Any]:
    """Concludes outbound call and greets client goodbye."""
    logger.info("Executing End Node")
    
    system_prompt = prompt_builder.build_prompt("system_prompt.txt")
    lang = state.get("language", "gujarati")
    
    conclude_text = (
        "Inquiry mate aabhar! Amara executive tamne details WhatsApp par share kari deshe. Have a great day!"
        if lang == "gujarati" else
        "Inquiry ke liye dhanyawad. Hamare executive aapse WhatsApp par contact karenge. Aapka din shubh rahe!"
        if lang == "hindi" else
        "Thank you for your time. Our sales executive will share the brochure via WhatsApp. Have a wonderful day!"
    )
    
    response = llm_service.generate(
        system_prompt,
        f"The conversation is ending. Do NOT say 'Hello' or introduce yourself. Thank the client politely and say goodbye. Language: {lang}. Suggestion: '{conclude_text}'"
    )
    
    return {
        "current_node": constants.Node.END,
        "agent_response": response,
        "messages": [{"role": "assistant", "content": response}]
    }
