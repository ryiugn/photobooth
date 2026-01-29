"""Activity logging utility."""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from models.activity_log import ActivityLog
from datetime import datetime
import json
import uuid


async def log_activity(
    db: AsyncSession,
    user_id: str,
    action: str,
    details: dict | None = None,
    request: Request | None = None
):
    """
    Log user activity to database.

    Args:
        db: Database session
        user_id: User ID who performed the action
        action: Action type (login, register, save_template, etc.)
        details: Additional details as dict
        request: FastAPI request object for IP/user agent
    """
    try:
        ip_address = None
        user_agent = None

        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        log_entry = ActivityLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        db.add(log_entry)
        await db.flush()  # Don't commit here, let caller handle it
    except Exception as e:
        # Don't raise - logging failures shouldn't break the app
        print(f"Failed to log activity: {e}")
