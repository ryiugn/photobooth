"""
Frame management routes for listing, uploading, and deleting photo frames.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import shutil
import uuid
from datetime import datetime

from config import settings
from routes.auth import get_current_user_dict

router = APIRouter()


# Response Models
class FrameInfo(BaseModel):
    """Information about a frame."""
    id: str
    name: str
    url: str
    thumbnail_url: Optional[str] = None
    created: str


class FramesListResponse(BaseModel):
    """Response containing list of frames."""
    frames: List[FrameInfo]


class FrameUploadResponse(BaseModel):
    """Response after frame upload."""
    id: str
    name: str
    url: str
    message: str = "Frame uploaded successfully"


# Utility Functions
def get_frames_dir() -> Path:
    """Get the frames directory path, creating if needed."""
    frames_dir = Path(settings.FRAMES_DIR)
    try:
        frames_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # On serverless platforms like Vercel, filesystem may be read-only
        pass
    return frames_dir


def generate_frame_id() -> str:
    """Generate a unique frame ID."""
    return f"frame_{uuid.uuid4().hex[:8]}"


# Routes
@router.get("", response_model=FramesListResponse)
async def list_frames(user: dict = Depends(get_current_user_dict)):
    """
    List all available frames.

    Returns:
        FramesListResponse with list of frame info
    """
    # On Vercel serverless, we return frames hosted on the frontend
    # Frontend serves static files from /frames/*.png
    frontend_url = settings.FRONTEND_URL.rstrip('/')

    # All available frames - hosted in the frontend's public/frames folder
    # These must match the actual files in web/public/frames/
    all_frames = [
        {
            "id": "frame_simple",
            "name": "Simple Pink",
            "filename": "frame_simple.png"
        },
        {
            "id": "frame_kawaii",
            "name": "Kawaii Pastel",
            "filename": "frame_kawaii.png"
        },
        {
            "id": "frame_classic",
            "name": "Classic Dark",
            "filename": "frame_classic.png"
        },
        {
            "id": "custom_pwumpd",
            "name": "Custom Pwumpd",
            "filename": "custom_20260127_095644_pwumpd.webp"
        },
        {
            "id": "custom_lyazbf",
            "name": "Custom Lyazbf",
            "filename": "custom_20260127_204241_lyazbf.PNG"
        },
        {
            "id": "custom_egptpm",
            "name": "Custom Egptpm",
            "filename": "custom_20260127_210302_egptpm.PNG"
        },
        {
            "id": "custom_hxgbqw",
            "name": "Custom Hxgbqw",
            "filename": "custom_20260127_210302_hxgbqw.PNG"
        },
        {
            "id": "custom_ieyzow",
            "name": "Custom Ieyzow",
            "filename": "custom_20260127_210302_ieyzow.PNG"
        },
        {
            "id": "custom_jhmwdz",
            "name": "Custom Jhmwdz",
            "filename": "custom_20260127_210302_jhmwdz.PNG"
        }
    ]

    frames = []
    for frame in all_frames:
        frame_url = f"{frontend_url}/frames/{frame['filename']}"
        frames.append(FrameInfo(
            id=frame['id'],
            name=frame['name'],
            url=frame_url,
            thumbnail_url=frame_url,
            created="2024-01-01T00:00:00"
        ))

    # Sort by name
    frames.sort(key=lambda f: f.name)

    return FramesListResponse(frames=frames)


@router.post("/upload", response_model=FrameUploadResponse)
async def upload_frame(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user_dict)
):
    """
    Upload a new frame image.

    Args:
        file: Uploaded image file

    Returns:
        FrameUploadResponse with frame info

    Raises:
        HTTPException: If file type is invalid
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    # Validate file extension
    valid_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in valid_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(valid_extensions)}"
        )

    # Generate unique frame ID and filename
    frame_id = generate_frame_id()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"custom_{timestamp}_{frame_id}{file_ext}"

    # Save file
    frames_dir = get_frames_dir()
    file_path = frames_dir / filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    frame_url = f"/api/v1/frames/{frame_id}/content"

    return FrameUploadResponse(
        id=frame_id,
        name=Path(file.filename).stem.replace('_', ' ').title(),
        url=frame_url,
        message="Frame uploaded successfully"
    )


@router.get("/{frame_id}/content")
async def get_frame_content(frame_id: str):
    """
    Get the actual frame image file.

    Args:
        frame_id: Frame identifier

    Returns:
        File response with the frame image

    Raises:
        HTTPException: If frame not found
    """
    frames_dir = get_frames_dir()

    # Find file by matching the frame_id
    for frame_file in frames_dir.glob("*"):
        if frame_id in frame_file.stem and frame_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
            from fastapi.responses import FileResponse
            return FileResponse(frame_file, media_type=f"image/{frame_file.suffix[1:]}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Frame '{frame_id}' not found"
    )


@router.delete("/{frame_id}")
async def delete_frame(frame_id: str, user: dict = Depends(get_current_user_dict)):
    """
    Delete a frame.

    Args:
        frame_id: Frame identifier

    Returns:
        Success message

    Raises:
        HTTPException: If frame not found
    """
    frames_dir = get_frames_dir()

    # Find and delete file
    for frame_file in frames_dir.glob("*"):
        if frame_id in frame_file.stem:
            frame_file.unlink()
            return {"message": f"Frame '{frame_id}' deleted successfully"}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Frame '{frame_id}' not found"
    )
