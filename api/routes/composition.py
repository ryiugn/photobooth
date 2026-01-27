"""
Composition routes for generating photostrips from multiple photos.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List
from pathlib import Path
import uuid
import io
from datetime import datetime

from config import settings
from routes.auth import get_current_user
from routes.camera import apply_frame_async, pil_to_base64

router = APIRouter()


# Request/Response Models
class ComposeRequest(BaseModel):
    """Request to compose photostrip."""
    session_id: str
    photo_ids: List[str]  # List of 4 photo IDs
    frame_paths: List[str]  # List of 4 frame paths


class ComposeResponse(BaseModel):
    """Response with composed photostrip."""
    strip_id: str
    photostrip_base64: str
    download_url: str


# Utility Functions
def generate_strip_id() -> str:
    """Generate a unique photostrip ID."""
    return f"strip_{uuid.uuid4().hex}"


async def compose_photostrip_bytes(photo_paths: List[Path], frame_paths: List[str], gap: int = 20) -> bytes:
    """
    Compose multiple photos into a vertical photostrip with frame overlays.

    Args:
        photo_paths: List of paths to captured photos
        frame_paths: List of paths to frame PNGs (one per photo)
        gap: Gap between photos in pixels

    Returns:
        Composed photostrip as bytes
    """
    from PIL import Image
    import cv2
    import numpy as np

    if len(photo_paths) != 4 or len(frame_paths) != 4:
        raise ValueError("Must have exactly 4 photos and 4 frames")

    # Load and frame each photo
    framed_photos = []
    for photo_path, frame_path in zip(photo_paths, frame_paths):
        # Load photo
        photo = cv2.imread(str(photo_path))
        if photo is None:
            raise ValueError(f"Failed to load photo: {photo_path}")

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
        framed_photos.append(final)

    # Get dimensions from first photo
    first_width, first_height = framed_photos[0].size

    # Calculate strip dimensions
    strip_width = first_width
    strip_height = (first_height * len(framed_photos)) + (gap * (len(framed_photos) - 1))

    # Create strip image
    photostrip = Image.new("RGB", (strip_width, strip_height))

    # Paste each photo vertically
    y_offset = 0
    for framed_photo in framed_photos:
        photostrip.paste(framed_photo, (0, y_offset))
        y_offset += first_height + gap

    # Convert to bytes
    img_bytes = io.BytesIO()
    photostrip.save(img_bytes, format='PNG', quality=settings.PHOTO_QUALITY)
    return img_bytes.getvalue()


async def save_photostrip(strip_bytes: bytes, strip_id: str) -> Path:
    """Save completed photostrip to disk."""
    strips_dir = Path(settings.STRIPS_DIR)
    strips_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"photostrip_{timestamp}_{strip_id}.png"
    file_path = strips_dir / filename

    with open(file_path, "wb") as f:
        f.write(strip_bytes)

    return file_path


# Routes
@router.post("", response_model=ComposeResponse)
async def compose_photostrip(
    request: ComposeRequest,
    user: dict = Depends(get_current_user)
):
    """
    Compose 4 captured photos into a vertical photostrip with frame overlays.

    Args:
        request: Composition request with session and photo IDs

    Returns:
        ComposeResponse with photostrip as base64

    Raises:
        HTTPException: If composition fails
    """
    # Validate exactly 4 photos
    if len(request.photo_ids) != 4 or len(request.frame_paths) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide exactly 4 photos and 4 frames"
        )

    # Load photo paths from session
    sessions_dir = Path(settings.SESSIONS_DIR) / request.session_id
    if not sessions_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{request.session_id}' not found"
        )

    photo_paths = []
    for i in range(4):
        photo_path = sessions_dir / f"photo_{i}.png"
        if not photo_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Photo {i} not found in session"
            )
        photo_paths.append(photo_path)

    # Compose photostrip
    try:
        strip_bytes = await compose_photostrip_bytes(photo_paths, request.frame_paths)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compose photostrip: {str(e)}"
        )

    # Save photostrip
    strip_id = generate_strip_id()
    strip_path = await save_photostrip(strip_bytes, strip_id)

    return ComposeResponse(
        strip_id=strip_id,
        photostrip_base64=pil_to_base64(strip_bytes),
        download_url=f"/api/v1/composition/download/{strip_id}"
    )


@router.get("/download/{strip_id}")
async def download_photostrip(strip_id: str, user: dict = Depends(get_current_user)):
    """
    Download a completed photostrip.

    Args:
        strip_id: Photostrip identifier

    Returns:
        File response with the photostrip image

    Raises:
        HTTPException: If photostrip not found
    """
    from fastapi.responses import FileResponse

    strips_dir = Path(settings.STRIPS_DIR)

    # Find strip file
    for strip_file in strips_dir.glob(f"*{strip_id}*.png"):
        return FileResponse(strip_file, media_type="image/png")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Photostrip '{strip_id}' not found"
    )
