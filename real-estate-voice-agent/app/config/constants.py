"""
Application-wide constants: node names, paths, status enums, and
qualification field definitions.
"""

import os
from enum import Enum

# ── Paths ──
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(APP_DIR)

KNOWLEDGE_DIR = os.path.join(APP_DIR, "knowledge")
PROMPTS_DIR = os.path.join(APP_DIR, "prompts")
STATIC_DIR = os.path.join(APP_DIR, "static")
AUDIO_DIR = os.path.join(STATIC_DIR, "audio")

# Ensure directories exist
for _d in (AUDIO_DIR, os.path.join(STATIC_DIR, "images")):
    os.makedirs(_d, exist_ok=True)


# ── Graph Node Names ──
class Node(str, Enum):
    GREETING = "greeting"
    PERMISSION = "permission"
    LANGUAGE_DETECTION = "language_detection"
    QUALIFICATION = "qualification"
    KNOWLEDGE = "knowledge"
    OBJECTION = "objection"
    BOOKING_DECISION = "booking_decision"
    BOOKING = "booking"
    FOLLOWUP = "followup"
    SUMMARY = "summary"
    END = "end"


# ── Lead / Booking Status ──
class LeadStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    QUALIFIED = "qualified"
    BOOKED = "booked"
    FOLLOW_UP = "follow_up"
    NOT_INTERESTED = "not_interested"


class BookingType(str, Enum):
    SITE_VISIT = "site_visit"
    FOLLOW_UP = "follow_up"


# ── Qualification Fields (collected one-at-a-time) ──
QUALIFICATION_FIELDS = [
    "budget",
    "preferred_location",
    "property_type",
    "purpose",
    "timeline",
]

# ── Supported Languages ──
SUPPORTED_LANGUAGES = ["gujarati", "hindi", "english"]
DEFAULT_LANGUAGE = "gujarati"
