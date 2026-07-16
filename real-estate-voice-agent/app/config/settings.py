"""
Application settings loaded from environment variables.
Uses pydantic-settings for type-safe configuration management.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration loaded from .env file."""

    # ── LLM Provider ──
    LLM_PROVIDER: str = Field(default="gemini", description="'openai' or 'gemini'")

    # ── OpenAI ──
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")

    # ── Google Gemini ──
    GOOGLE_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")

    # ── Deepgram STT ──
    DEEPGRAM_API_KEY: str = Field(default="")

    # ── Sarvam Bulbul TTS ──
    SARVAM_API_KEY: str = Field(default="")

    # ── Database ──
    DATABASE_URL: str = Field(default="sqlite:///./data/leads.db")

    # ── Server ──
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
