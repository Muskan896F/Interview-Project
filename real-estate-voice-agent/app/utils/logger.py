"""
Structured logging configuration for the application.
Provides a single ``get_logger`` factory and a pre-built default ``logger``.
"""

import logging
import sys
from app.config.settings import settings


def get_logger(name: str = "voice_agent") -> logging.Logger:
    """Return a configured logger; avoids duplicate handlers."""
    _logger = logging.getLogger(name)
    if _logger.hasHandlers():
        return _logger

    _logger.setLevel(settings.LOG_LEVEL.upper())

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    _logger.addHandler(handler)
    return _logger


logger = get_logger()
