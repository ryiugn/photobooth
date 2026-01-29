"""Admin-only endpoints for system management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from models.base import get_db
from models.user import User, UserRole
from models.activity_log import ActivityLog
from models.template import Template
from models.custom_frame import CustomFrame
from routes.users import get_current_user

router = APIRouter()


class CleanupResponse(BaseModel):
    """Cleanup response."""
    success: bool
    deleted_count: int


class StatsResponse(BaseModel):
    """System statistics response."""
    total_users: int
    total_templates: int
    total_custom_frames: int
    new_users_today: int
    photos_captured_today: int


@router.post("/cleanup-logs", response_model=CleanupResponse)
async def cleanup_logs(db: AsyncSession = Depends(get_db)):
    """Delete activity logs older than 7 days."""
    cutoff = datetime.utcnow() - timedelta(days=7)

    # Delete old logs
    stmt = delete(ActivityLog).where(ActivityLog.created_at < cutoff)
    result = await db.execute(stmt)
    await db.commit()

    return CleanupResponse(success=True, deleted_count=result.rowcount or 0)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system statistics (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Total counts
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_templates = (await db.execute(select(func.count(Template.id)))).scalar() or 0
    total_custom_frames = (await db.execute(select(func.count(CustomFrame.id)))).scalar() or 0

    # New users today
    new_users_today = (
        await db.execute(
            select(func.count(User.id)).where(User.created_at >= today_start)
        )
    ).scalar() or 0

    # Photos captured today
    photos_captured_today = (
        await db.execute(
            select(func.count(ActivityLog.id)).where(
                and_(
                    ActivityLog.action == "capture_photo",
                    ActivityLog.created_at >= today_start
                )
            )
        )
    ).scalar() or 0

    return StatsResponse(
        total_users=total_users,
        total_templates=total_templates,
        total_custom_frames=total_custom_frames,
        new_users_today=new_users_today,
        photos_captured_today=photos_captured_today
    )
