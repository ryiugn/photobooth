"""Custom frame upload endpoints."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.base import get_db
from models.custom_frame import CustomFrame
from models.user import User
from routes.users import get_current_user
from lib.storage import storage_service
from lib.logger import log_activity
from PIL import Image
from io import BytesIO
from typing import List

router = APIRouter()


class CustomFrameResponse(BaseModel):
    """Custom frame response."""
    id: str
    name: str
    storage_path: str
    thumbnail_path: str | None
    is_public: bool
    width: int
    height: int
    created_at: str


class CustomFrameListResponse(BaseModel):
    """Custom frames list response."""
    frames: List[CustomFrameResponse]


# Valid MIME types
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MIN_DIMENSIONS = (800, 1200)  # Minimum width, height


@router.post("/upload", response_model=CustomFrameResponse, status_code=201)
async def upload_custom_frame(
    file: UploadFile = File(...),
    name: str = Form(...),
    is_public: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a custom frame."""
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_TYPES)}"
        )

    # Read and validate file
    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Validate image dimensions
    try:
        image = Image.open(BytesIO(contents))
        width, height = image.size

        if width < MIN_DIMENSIONS[0] or height < MIN_DIMENSIONS[1]:
            raise HTTPException(
                status_code=400,
                detail=f"Image too small. Minimum: {MIN_DIMENSIONS[0]}x{MIN_DIMENSIONS[1]}"
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image file") from e

    # Upload to Vercel Blob
    try:
        upload_result = await storage_service.upload_image(
            contents,
            file.filename or "frame.png",
            current_user.id,
            file.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") from e

    # Create database record
    custom_frame = CustomFrame(
        user_id=current_user.id,
        name=name,
        storage_path=upload_result["url"],
        thumbnail_path=upload_result["thumbnail_url"],
        is_public=is_public,
        file_size_bytes=upload_result["file_size"],
        width=upload_result["width"],
        height=upload_result["height"]
    )
    db.add(custom_frame)

    try:
        await db.commit()
        await db.refresh(custom_frame)
    except Exception:
        await db.rollback()
        raise

    # Log activity
    await log_activity(db, current_user.id, "upload_frame", {
        "frame_id": custom_frame.id,
        "frame_name": name
    })

    return CustomFrameResponse(
        id=custom_frame.id,
        name=custom_frame.name,
        storage_path=custom_frame.storage_path,
        thumbnail_path=custom_frame.thumbnail_path,
        is_public=custom_frame.is_public,
        width=custom_frame.width,
        height=custom_frame.height,
        created_at=custom_frame.created_at.isoformat()
    )


@router.get("/custom", response_model=CustomFrameListResponse)
async def list_custom_frames(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List custom frames available to current user."""
    result = await db.execute(
        select(CustomFrame).where(
            (CustomFrame.user_id == current_user.id) | (CustomFrame.is_public == True)
        ).order_by(CustomFrame.created_at.desc())
    )
    frames = result.scalars().all()

    return CustomFrameListResponse(
        frames=[
            CustomFrameResponse(
                id=f.id,
                name=f.name,
                storage_path=f.storage_path,
                thumbnail_path=f.thumbnail_path,
                is_public=f.is_public,
                width=f.width,
                height=f.height,
                created_at=f.created_at.isoformat()
            )
            for f in frames
        ]
    )


@router.delete("/custom/{frame_id}")
async def delete_custom_frame(
    frame_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a custom frame."""
    result = await db.execute(
        select(CustomFrame).where(CustomFrame.id == frame_id)
    )
    frame = result.scalar_one_or_none()

    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")

    # Check ownership
    if frame.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Not your frame")

    # Delete from storage
    await storage_service.delete_file(frame.storage_path)
    if frame.thumbnail_path:
        await storage_service.delete_file(frame.thumbnail_path)

    # Delete from database
    await db.delete(frame)
    await db.commit()

    # Log activity
    await log_activity(db, current_user.id, "delete_frame", {
        "frame_id": frame_id,
        "frame_name": frame.name
    })

    return {"message": "Frame deleted successfully"}
