"""
General-purpose helper utilities.
"""

import uuid
import json
from datetime import datetime
from typing import Any, Dict


def generate_session_id() -> str:
    """Return a new UUID-based session identifier."""
    return uuid.uuid4().hex[:16]


def now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.utcnow().isoformat()


def safe_json_loads(text: str, fallback: Any = None) -> Any:
    """Parse JSON; return *fallback* on failure instead of raising."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return fallback


def clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Strip keys whose value is ``None``."""
    return {k: v for k, v in data.items() if v is not None}


def truncate(text: str, max_len: int = 200) -> str:
    """Shorten text for log messages."""
    return text if len(text) <= max_len else text[:max_len] + "…"
