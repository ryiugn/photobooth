"""
Configuration module for the Photobooth API.
"""

from pydantic import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App Configuration
    APP_NAME: str = "Photobooth API"
    DEBUG: bool = False

    # Authentication
    PIN_HASH: str = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7TiK.MnKHq"  # Default: "1234"
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "photobooth"

    # File Storage (local fallback)
    FRAMES_DIR: str = "project_files/frames"
    TEMPLATES_DIR: str = "project_files/templates"
    UPLOADS_DIR: str = "project_files/uploads"
    SESSIONS_DIR: str = "project_files/sessions"
    STRIPS_DIR: str = "project_files/strips"

    # Camera/Processing
    MAX_PHOTO_SIZE_MB: int = 10
    PHOTO_QUALITY: int = 95

    # Rate Limiting
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_SECONDS: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings
settings = get_settings()
