"""Cron job authentication middleware."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from config import settings


class CronAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to verify cron job requests."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/v1/admin/cleanup"):
            auth_header = request.headers.get("authorization", "")
            expected = f"Bearer {settings.CRON_SECRET}"

            if auth_header != expected:
                raise HTTPException(status_code=401, detail="Unauthorized")

        return await call_next(request)
