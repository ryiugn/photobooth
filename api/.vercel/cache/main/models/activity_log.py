"""Activity log model for tracking user actions."""

from sqlalchemy import String, DateTime, ForeignKey, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base
import uuid


class ActivityLog(Base):
    """Activity log entry for audit trail."""

    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False, index=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_activity_logs_user_id_created_at", "user_id", "created_at"),
    )
