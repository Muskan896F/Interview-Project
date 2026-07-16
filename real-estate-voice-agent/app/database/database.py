"""
SQLAlchemy engine, session factory, and base class.
Auto-creates the ``data/`` directory for SQLite.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config.settings import settings

# Ensure the data directory exists for SQLite
_db_url = settings.DATABASE_URL
if _db_url.startswith("sqlite:///"):
    _db_path = _db_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(_db_path) or ".", exist_ok=True)

engine = create_engine(
    _db_url,
    connect_args={"check_same_thread": False} if _db_url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a session then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
