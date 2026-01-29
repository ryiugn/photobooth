"""Activity logging and query endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List, Optional
from models.base import get_db
from models.activity_log import ActivityLog
from models.user import User
from routes.users import get_current_user
from lib.logger import log_activity
import uuid

router = APIRouter()


class ActivityLogRequest(BaseModel):
    """Activity log request from client."""
    action: str
    details: Optional[dict] = None


class ActivityLogResponse(BaseModel):
    """Activity log entry response."""
    id: str
    timestamp: str
    user_email: str
    user_name: str
    action: str
    details: str | None
    ip_address: str | None


class ActivityListResponse(BaseModel):
    """Activity logs list response."""
    logs: List[ActivityLogResponse]
    total: int


@router.post("")
async def create_activity_log(
    request: ActivityLogRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Log user activity (authenticated users only)."""
    await log_activity(
        db=db,
        user_id=current_user.id,
        action=request.action,
        details=request.details,
        request=http_request
    )
    await db.commit()
    return {"success": True}


@router.get("", response_model=ActivityListResponse)
async def get_activity_logs(
    user_id: str | None = Query(None),
    action: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get activity logs (admin only)."""
    # Admin check
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Build where clause
    conditions = []

    if user_id:
        conditions.append(ActivityLog.user_id == user_id)

    if action:
        conditions.append(ActivityLog.action == action)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            conditions.append(ActivityLog.created_at >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            conditions.append(ActivityLog.created_at <= end_dt)
        except ValueError:
            pass

    where_clause = and_(*conditions) if conditions else None

    # Query logs with user info
    query = (
        select(ActivityLog, User)
        .join(User, ActivityLog.user_id == User.id)
        .order_by(ActivityLog.created_at.desc())
    )

    if where_clause is not None:
        query = query.where(where_clause)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)

    logs = []
    for log, user in result:
        logs.append(ActivityLogResponse(
            id=log.id,
            timestamp=log.created_at.isoformat(),
            user_email=user.email,
            user_name=user.name,
            action=log.action,
            details=log.details,
            ip_address=log.ip_address
        ))

    return ActivityListResponse(logs=logs, total=total)
