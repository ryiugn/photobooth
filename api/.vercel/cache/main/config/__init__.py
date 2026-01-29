"""
Configuration module for the Photobooth API.
"""

import os


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # App Configuration
        self.APP_NAME = os.getenv("APP_NAME", "Photobooth API")
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"

        # Database
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/photobooth"
        )

        # Authentication
        self.PIN_HASH = os.getenv("PIN_HASH", "$2b$12$MvoY/xwcjRW2fNUZ2Kr0AeZk6A/dZL2v1QiT1RDpC75BFEP6o7t4a")
        self.JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

        # CORS
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]
        if self.FRONTEND_URL not in self.ALLOWED_ORIGINS:
            self.ALLOWED_ORIGINS.append(self.FRONTEND_URL)

        # File Storage (local)
        self.FRAMES_DIR = os.getenv("FRAMES_DIR", "project_files/frames")
        self.TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "project_files/templates")
        self.UPLOADS_DIR = os.getenv("UPLOADS_DIR", "project_files/uploads")
        self.SESSIONS_DIR = os.getenv("SESSIONS_DIR", "project_files/sessions")
        self.STRIPS_DIR = os.getenv("STRIPS_DIR", "project_files/strips")

        # Processing
        self.MAX_PHOTO_SIZE_MB = int(os.getenv("MAX_PHOTO_SIZE_MB", "10"))
        self.PHOTO_QUALITY = int(os.getenv("PHOTO_QUALITY", "95"))

        # Rate Limiting
        self.MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.LOCKOUT_DURATION_SECONDS = int(os.getenv("LOCKOUT_DURATION_SECONDS", "300"))

        # Google OAuth
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
        self.GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")

        # Cron Job
        self.CRON_SECRET = os.getenv("CRON_SECRET", "change-me-in-production")


# Export settings singleton
settings = Settings()
