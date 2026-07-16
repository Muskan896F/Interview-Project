"""
CRUD helpers wrapping SQLAlchemy queries for Lead, Conversation,
Booking, and Summary tables.
"""

import json
import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.database import models
from app.database.schema import (
    LeadCreate, BookingCreate, SummaryCreate,
)
from app.utils.logger import logger


# ── Lead ──
def create_lead(db: Session, data: LeadCreate) -> models.Lead:
    lead = models.Lead(
        name=data.name,
        phone=data.phone,
        email=data.email,
        source=data.source or "web_form",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    logger.info("Created lead id=%s phone=%s", lead.id, lead.phone)
    return lead


def get_lead_by_phone(db: Session, phone: str) -> Optional[models.Lead]:
    return db.query(models.Lead).filter(models.Lead.phone == phone).first()


def get_lead_by_id(db: Session, lead_id: int) -> Optional[models.Lead]:
    return db.query(models.Lead).filter(models.Lead.id == lead_id).first()


def update_lead_status(db: Session, lead_id: int, status: str) -> Optional[models.Lead]:
    lead = get_lead_by_id(db, lead_id)
    if lead:
        lead.status = status
        lead.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(lead)
    return lead


def get_all_leads(db: Session) -> List[models.Lead]:
    return db.query(models.Lead).order_by(models.Lead.created_at.desc()).all()


# ── Conversation ──
def create_conversation(
    db: Session,
    session_id: str,
    lead_id: int,
    state_dict: Dict[str, Any],
) -> models.Conversation:
    conv = models.Conversation(
        session_id=session_id,
        lead_id=lead_id,
        language=state_dict.get("language", "gujarati"),
        current_node=state_dict.get("current_node", "greeting"),
        state_json=state_dict,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation(db: Session, session_id: str) -> Optional[models.Conversation]:
    return (
        db.query(models.Conversation)
        .filter(models.Conversation.session_id == session_id)
        .first()
    )


def update_conversation_state(
    db: Session, session_id: str, state_dict: Dict[str, Any]
) -> Optional[models.Conversation]:
    conv = get_conversation(db, session_id)
    if conv:
        conv.state_json = state_dict
        conv.current_node = state_dict.get("current_node", conv.current_node)
        conv.language = state_dict.get("language", conv.language)
        db.commit()
        db.refresh(conv)
    return conv


def end_conversation(db: Session, session_id: str) -> Optional[models.Conversation]:
    conv = get_conversation(db, session_id)
    if conv:
        conv.ended_at = datetime.datetime.utcnow()
        conv.current_node = "end"
        db.commit()
        db.refresh(conv)
    return conv


# ── Booking ──
def create_booking(db: Session, data: BookingCreate) -> models.Booking:
    booking = models.Booking(
        lead_id=data.lead_id,
        session_id=data.session_id,
        booking_type=data.booking_type,
        date=data.date,
        time=data.time,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    logger.info("Booking created id=%s type=%s", booking.id, booking.booking_type)
    return booking


def get_bookings_by_lead(db: Session, lead_id: int) -> List[models.Booking]:
    return (
        db.query(models.Booking)
        .filter(models.Booking.lead_id == lead_id)
        .order_by(models.Booking.created_at.desc())
        .all()
    )


# ── Summary ──
def upsert_summary(db: Session, data: SummaryCreate) -> models.Summary:
    existing = (
        db.query(models.Summary)
        .filter(models.Summary.session_id == data.session_id)
        .first()
    )
    if existing:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    summary = models.Summary(**data.model_dump())
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def get_summary(db: Session, session_id: str) -> Optional[models.Summary]:
    return (
        db.query(models.Summary)
        .filter(models.Summary.session_id == session_id)
        .first()
    )
