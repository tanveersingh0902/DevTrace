"""
DevTrace Configuration Module.

This module handles all application configuration using pydantic-settings.
Configuration values can come from:
1. Environment variables (highest priority)
2. A .env file
3. Default values defined here

WHY pydantic-settings?
- Type-safe configuration (no more "is this string or int?")
- Automatic environment variable loading
- Validation at startup (fail fast if config is wrong)
- Secrets never hardcoded — always from environment
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "DevTrace"
    app_version: str = "0.1.0"
    debug: bool = False

    # API
    api_prefix: str = "/api/v1"

    # CORS — which origins can call our API
    # In development, the React dev server runs on localhost:5173
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database
    database_url: str = "sqlite:///devtrace.db"

    # Scanner
    max_file_size_bytes: int = 1_000_000  # 1 MB — skip huge generated files
    max_files: int = 10_000  # Safety limit for very large repos

    # Optional AI features (Phase 3)
    openai_api_key: str | None = None


# Singleton instance — import this throughout the app
settings = Settings()

