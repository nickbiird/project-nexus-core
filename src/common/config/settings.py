"""
Project Nexus — Application Settings
=====================================

Pydantic BaseSettings for type-safe configuration from .env files.
All secrets and configuration values are loaded here and injected
into application modules via dependency injection.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class NexusSettings(BaseSettings):
    """Root configuration for all Project Nexus services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_log_level: str = "DEBUG"
    app_secret_key: str = "CHANGE_ME_IN_PRODUCTION"

    # --- LLM Providers ---
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: Literal["openai", "anthropic"] = "openai"
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 4096

    # --- Database ---
    database_url: str = "sqlite:///data/yellowbird.db"

    # --- WhatsApp ---
    whatsapp_provider: Literal["360dialog", "twilio"] = "360dialog"
    whatsapp_api_key: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = "nexus_webhook_verify_token"

    # --- Cost Controls ---
    llm_cost_limit_per_run_usd: float = 2.00
    llm_cost_limit_per_query_usd: float = 0.05
    llm_cost_alert_threshold_usd: float = 50.00

    # --- Streamlit ---
    streamlit_server_port: int = 8501

    # --- FastAPI ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1


@lru_cache(maxsize=1)
def get_settings() -> NexusSettings:
    """Singleton settings instance (cached after first call)."""
    return NexusSettings()
