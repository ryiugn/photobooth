"""
Camera routes for capturing photos with frame overlay.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import uuid
import io
from datetime import datetime

from config import settings
from routes.auth import get_current_user

router = APIRouter()


# Response Models
class CaptureResponse(BaseModel):
    """Response after photo capture with frame applied."""
    photo_id: str
    framed_photo: str  # Base64 encoded image
    frame_used: str


# Utility Functions
async def save_temp_photo(session_id: str, index: int, file_data: bytes) -> Path:
    """Save a temporary photo to disk."""
    sessions_dir = Path(settings.SESSIONS_DIR) / session_id
    sessions_dir.mkdir(parents=True, exist_ok=True)

    filename = f"photo_{index}.png"
    file_path = sessions_dir / filename

    with open(file_path, "wb") as f:
        f.write(file_data)

    return file_path


def generate_photo_id() -> str:
    """Generate a unique photo ID."""
    return f"photo_{uuid.uuid4().hex}"


async def apply_frame_async(photo_path: Path, frame_path: str) -> bytes:
    """Apply frame to photo and return as bytes."""
    from PIL import Image
    import cv2
    import numpy as np

    # Load photo
    photo = cv2.imread(str(photo_path))
    if photo is None:
        raise ValueError("Failed to load photo")

    # Convert BGR to RGB
    rgb_photo = cv2.cvtColor(photo, cv2.COLOR_BGR2RGB)
    photo_pil = Image.fromarray(rgb_photo)

    # Load frame
    frame = Image.open(frame_path).convert("RGBA")

    # Get dimensions
    photo_width, photo_height = photo_pil.size
    frame_width, frame_height = frame.size

    # Calculate scaling to cover photo
    scale_x = photo_width / frame_width
    scale_y = photo_height / frame_height
    scale = max(scale_x, scale_y)

    # Scale frame
    scaled_frame_width = int(frame_width * scale)
    scaled_frame_height = int(frame_height * scale)
    frame_scaled = frame.resize((scaled_frame_width, scaled_frame_height), Image.Resampling.LANCZOS)

    # Crop frame to match photo dimensions
    crop_x = (scaled_frame_width - photo_width) // 2
    crop_y = (scaled_frame_height - photo_height) // 2
    frame_cropped = frame_scaled.crop((crop_x, crop_y, crop_x + photo_width, crop_y + photo_height))

    # Scale photo to fit within frame (contain)
    photo_scale_x = photo_width / photo_pil.width
    photo_scale_y = photo_height / photo_pil.height
    photo_scale = min(photo_scale_x, photo_scale_y)

    final_photo_width = int(photo_pil.width * photo_scale)
    final_photo_height = int(photo_pil.height * photo_scale)
    photo_scaled = photo_pil.resize((final_photo_width, final_photo_height), Image.Resampling.LANCZOS)

    # Center photo
    photo_x = (photo_width - final_photo_width) // 2
    photo_y = (photo_height - final_photo_height) // 2

    # Create composition
    composed = Image.new("RGBA", (photo_width, photo_height))
    composed.paste(photo_scaled, (photo_x, photo_y))
    composed.paste(frame_cropped, (0, 0), frame_cropped)

    # Convert to RGB
    final = composed.convert("RGB")

    # Convert to bytes
    img_bytes = io.BytesIO()
    final.save(img_bytes, format='PNG', quality=settings.PHOTO_QUALITY)
    return img_bytes.getvalue()


def pil_to_base64(image_bytes: bytes) -> str:
    """Convert PIL image bytes to base64 string."""
    import base64
    return f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"


# Routes
@router.post("", response_model=CaptureResponse)
async def capture_photo(
    photo: UploadFile = File(...),
    frame_index: int = Form(...),
    session_id: str = Form(...),
    user: dict = Depends(get_current_user)
):
    """
    Capture a photo and apply the specified frame overlay.

    Args:
        photo: Uploaded photo file
        frame_index: Index of the frame to apply (0-3)
        session_id: Session identifier for temporary storage

    Returns:
        CaptureResponse with framed photo as base64

    Raises:
        HTTPException: If processing fails
    """
    # Validate frame index
    if frame_index < 0 or frame_index > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Frame index must be between 0 and 3"
        )

    # Read photo data
    photo_data = await photo.read()

    # Validate file size
    max_size = settings.MAX_PHOTO_SIZE_MB * 1024 * 1024
    if len(photo_data) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Photo too large. Maximum size: {settings.MAX_PHOTO_SIZE_MB}MB"
        )

    # Save temp photo
    photo_path = await save_temp_photo(session_id, frame_index, photo_data)

    # Get frame path from session (this would be stored when session starts)
    # For now, use a default frame
    frames_dir = Path(settings.FRAMES_DIR)
    frame_files = list(frames_dir.glob("*.png"))
    if not frame_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No frames available"
        )

    # Use the frame at the specified index
    frame_path = str(frame_files[frame_index % len(frame_files)])

    # Apply frame
    try:
        framed_photo_bytes = await apply_frame_async(photo_path, frame_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply frame: {str(e)}"
        )

    photo_id = generate_photo_id()

    return CaptureResponse(
        photo_id=photo_id,
        framed_photo=pil_to_base64(framed_photo_bytes),
        frame_used=frame_path
    )
