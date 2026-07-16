"""
JSON Export Service
───────────────────
Exports live DB data to data/conversations.json and data/summaries.json
after every conversation turn and after every summary save.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.database import models
from app.utils.logger import logger

# ── File paths ──
_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
)
CONVERSATIONS_JSON = os.path.join(_DATA_DIR, "conversations.json")
SUMMARIES_JSON = os.path.join(_DATA_DIR, "summaries.json")


def _safe_dt(dt) -> str | None:
    """Convert datetime to ISO string safely."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def export_conversations(db: Session) -> None:
    """
    Reads all conversations from the DB (with their full state_json / messages)
    and writes them to data/conversations.json.
    Called after every /api/chat turn.
    """
    try:
        conversations = (
            db.query(models.Conversation)
            .order_by(models.Conversation.started_at.desc())
            .all()
        )

        export_list = []
        for conv in conversations:
            state: Dict[str, Any] = conv.state_json or {}
            messages = state.get("messages", [])

            export_list.append({
                "session_id": conv.session_id,
                "lead_id": conv.lead_id,
                "language": conv.language,
                "current_node": conv.current_node,
                "started_at": _safe_dt(conv.started_at),
                "ended_at": _safe_dt(conv.ended_at),
                # Lead qualification fields captured so far
                "qualification": {
                    "budget": state.get("budget", ""),
                    "preferred_location": state.get("preferred_location", ""),
                    "property_type": state.get("property_type", ""),
                    "purpose": state.get("purpose", ""),
                    "timeline": state.get("timeline", ""),
                },
                # Full dialogue transcript
                "messages": messages,
            })

        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(CONVERSATIONS_JSON, "w", encoding="utf-8") as f:
            json.dump(export_list, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(export_list)} conversation(s) to conversations.json")

    except Exception as e:
        logger.error(f"Failed to export conversations.json: {e}")


def export_summaries(db: Session) -> None:
    """
    Reads all summaries from the DB and writes them to data/summaries.json.
    Called when a call ends and a summary is saved.
    """
    try:
        summaries = (
            db.query(models.Summary)
            .order_by(models.Summary.created_at.desc())
            .all()
        )

        export_list = []
        for s in summaries:
            export_list.append({
                "session_id": s.session_id,
                "lead_id": s.lead_id,
                "lead_score": s.lead_score,
                "interested": s.interested,
                "budget": s.budget,
                "preferred_location": s.preferred_location,
                "property_type": s.property_type,
                "purpose": s.purpose,
                "timeline": s.timeline,
                "questions_asked": s.questions_asked or [],
                "objections": s.objections or [],
                "booking_status": s.booking_status,
                "follow_up_status": s.follow_up_status,
                "summary_text": s.summary_text,
                "created_at": _safe_dt(s.created_at),
            })

        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(SUMMARIES_JSON, "w", encoding="utf-8") as f:
            json.dump(export_list, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(export_list)} summary/summaries to summaries.json")

    except Exception as e:
        logger.error(f"Failed to export summaries.json: {e}")


export_service_instance = None  # imported directly, no singleton needed
