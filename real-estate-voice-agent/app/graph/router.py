from app.graph.state import ConversationState
from app.config import constants
from app.utils.logger import logger

def route_next_node(state: ConversationState) -> str:
    """
    Routes the workflow to the correct node for the current turn.
    Uses state['current_node'] as the previous node, and state['last_message'] to decide.
    """
    prev_node = state.get("current_node", constants.Node.GREETING)
    last_msg = state.get("last_message", "").lower().strip()
    
    logger.info(f"Routing next node. Previous Node: '{prev_node}', User Input: '{last_msg}'")

    # 1. First Turn: If no user input has occurred yet, always start with GREETING
    if not last_msg and prev_node == constants.Node.GREETING:
        return constants.Node.GREETING

    # 2. Global Intercepts: If user asks a genuine knowledge question about the project
    # IMPORTANT: Do NOT intercept if we are mid-qualification collecting an answer.
    # Only trigger on messages that are genuine questions (not qualification answers like "40 lakh" or "3 BHK")
    question_triggers = [
        "what is", "how much", "when will", "is there", "do you have",
        "possession", "amenit", "loan", "builder",
        "rera", "discount", "offer", "hospital", "school", "parking",
        "price ketli", "ketla ma", "kyare malse", "facilit",
        "price of", "cost of", "tell me about"
    ]
    # Only route to KNOWLEDGE if the message looks like a genuine question,
    # not a short qualification answer.
    # We check for multi-word question starters, or if it has "?" combined with a question-indicative keyword.
    question_keywords = [
        "what", "how", "when", "where", "who", "which", "why", "price", "cost", "possession", "rera",
        "amenit", "loan", "builder", "discount", "offer", "hospital", "school", "parking", "facilit",
        "availab", "sq", "feet", "foot", "carpet", "size", "map", "locat", "brochure", "detail",
        "kyare", "ketla", "ketli", "bhada", "rent", "interest", "bank"
    ]
    has_question_keyword = any(w in last_msg for w in question_keywords)
    
    is_question = (
        # Multi-word triggers like "what is" can trigger without a "?"
        any(trigger in last_msg for trigger in question_triggers if len(trigger.split()) > 1)
        or
        # A "?" alone is not enough; it must be accompanied by a question keyword to filter out rising-intonation answers (e.g. "next month?")
        ("?" in last_msg and has_question_keyword)
    )
    if is_question and prev_node not in [
        constants.Node.KNOWLEDGE,
        constants.Node.GREETING,
        constants.Node.PERMISSION
    ]:
        return constants.Node.KNOWLEDGE

    # 3. Global Intercepts: If user raises an objection / is busy
    objection_triggers = [
        "busy", "later", "not interested", "budget high", "expensive",
        "family discuss", "discuss with family", "pachi vaat", "tem time",
        "varthani", "nathi levo", "budget vadhi", "biji var", "call back"
    ]
    if any(trigger in last_msg for trigger in objection_triggers):
        if prev_node != constants.Node.OBJECTION:
            return constants.Node.OBJECTION

    # 4. Turn-based routing logic based on previous execution node
    if prev_node == constants.Node.GREETING:
        # If customer declined to talk during the greeting → end gracefully
        denial_words = ["no", "nahi", "na", "busy", "not now", "pachi", "later", "nathi", "abhi nahi", "nai"]
        if any(w in last_msg for w in denial_words):
            return constants.Node.END
        return constants.Node.PERMISSION

    if prev_node == constants.Node.PERMISSION:
        denial_words = ["no", "nahi", "na", "busy", "not now", "pachi", "later", "nathi", "abhi nahi", "nai"]
        if any(w in last_msg for w in denial_words):
            return constants.Node.END
        return constants.Node.QUALIFICATION


    if prev_node == constants.Node.QUALIFICATION:
        # Check if all qualification fields are present
        missing_field = None
        for field in constants.QUALIFICATION_FIELDS:
            if not state.get(field):
                missing_field = field
                break
        if missing_field:
            return constants.Node.QUALIFICATION
        return constants.Node.BOOKING_DECISION

    if prev_node in [constants.Node.KNOWLEDGE, constants.Node.OBJECTION]:
        # After answering a question or handling an objection, check if they are busy
        if "call back" in last_msg or "later" in last_msg or "pachi" in last_msg or "busy" in last_msg:
            return constants.Node.FOLLOWUP
            
        # Otherwise, resume qualification or booking decision
        missing_field = None
        for field in constants.QUALIFICATION_FIELDS:
            if not state.get(field):
                missing_field = field
                break
        if missing_field:
            return constants.Node.QUALIFICATION
        return constants.Node.BOOKING_DECISION

    if prev_node == constants.Node.BOOKING_DECISION:
        agree_words = ["yes", "sure", "book", "saturday", "sunday", "weekend", "haa", "karvi chhe", "visit", "ok"]
        if any(w in last_msg for w in agree_words):
            return constants.Node.BOOKING
        return constants.Node.FOLLOWUP

    if prev_node == constants.Node.BOOKING:
        # If we have booking date and time in state, complete to summary
        if state.get("booking_date") and state.get("booking_time"):
            return constants.Node.SUMMARY
        return constants.Node.BOOKING

    if prev_node == constants.Node.FOLLOWUP:
        if state.get("followup_date") and state.get("followup_time"):
            return constants.Node.SUMMARY
        return constants.Node.FOLLOWUP

    if prev_node == constants.Node.SUMMARY:
        return constants.Node.END

    return constants.Node.END

