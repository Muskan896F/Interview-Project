"""
Input validators for phone numbers, emails, and dates.
"""

import re
from typing import Optional


def validate_phone(phone: str) -> bool:
    """Accept Indian mobile numbers (10 digits, optional +91 prefix)."""
    if not phone:
        return False
    cleaned = re.sub(r"[\s\-()]", "", phone)
    return bool(re.match(r"^(\+91)?[6-9]\d{9}$", cleaned))


def validate_email(email: str) -> bool:
    """Basic RFC-style email validation."""
    if not email:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email))


def validate_date(date_str: str) -> bool:
    """Check DD-MM-YYYY or DD/MM/YYYY format."""
    if not date_str:
        return False
    return bool(re.match(r"^\d{1,2}[/-]\d{1,2}[/-]\d{4}$", date_str))


def sanitize_phone(phone: str) -> Optional[str]:
    """Return a cleaned 10-digit phone string, or None."""
    if not phone:
        return None
    cleaned = re.sub(r"[^\d]", "", phone)
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    return cleaned if len(cleaned) == 10 else None
