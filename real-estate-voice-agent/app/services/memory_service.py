from sqlalchemy.orm import Session
from app.database import crud, schema
from app.utils.logger import logger

class MemoryService:
    """Service to load and store state metrics and CRM logs between dialogue turns."""

    def load_conversation_state(self, session_id: str, db: Session) -> dict:
        """Load conversation state dictionary from SQLite database."""
        db_conv = crud.get_conversation(db, session_id)
        if db_conv and db_conv.state_json:
            logger.info(f"Loaded existing session state from DB for session: {session_id}")
            return db_conv.state_json
        return {}

    def save_conversation_state(self, session_id: str, lead_id: int, state_dict: dict, db: Session) -> None:
        """Save conversation state dictionary to SQLite database."""
        db_conv = crud.get_conversation(db, session_id)
        if db_conv:
            crud.update_conversation_state(db, session_id, state_dict)
            logger.info(f"Updated session state in DB for session: {session_id}")
        else:
            crud.create_conversation(db, session_id, lead_id, state_dict)
            logger.info(f"Created new session state in DB for session: {session_id}")

    def save_booking(self, lead_id: int, session_id: str, booking_type: str, date: str, time: str, db: Session) -> None:
        """Create a booking row in SQLite database."""
        booking_data = schema.BookingCreate(
            lead_id=lead_id,
            session_id=session_id,
            booking_type=booking_type,
            date=date,
            time=time
        )
        crud.create_booking(db, booking_data)
        
        # Also update the corresponding lead status in DB
        status = "booked" if booking_type == "site_visit" else "follow_up"
        crud.update_lead_status(db, lead_id, status)
        logger.info(f"Created database booking entry ({booking_type}) for lead id: {lead_id}")

    def save_summary(self, session_id: str, lead_id: int, summary_data: dict, db: Session) -> None:
        """Create or update database summary and lead score values."""
        summary_create = schema.SummaryCreate(
            session_id=session_id,
            lead_id=lead_id,
            lead_score=summary_data.get("lead_score", 0),
            interested=summary_data.get("interested"),
            budget=summary_data.get("budget"),
            preferred_location=summary_data.get("preferred_location"),
            property_type=summary_data.get("property_type"),
            purpose=summary_data.get("purpose"),
            timeline=summary_data.get("timeline"),
            questions_asked=summary_data.get("questions_asked"),
            objections=summary_data.get("objections"),
            booking_status=summary_data.get("booking_status"),
            follow_up_status=summary_data.get("follow_up_status"),
            summary_text=summary_data.get("summary_text")
        )
        crud.upsert_summary(db, summary_create)
        logger.info(f"Upserted database summary logs for session: {session_id}")

memory_service = MemoryService()
