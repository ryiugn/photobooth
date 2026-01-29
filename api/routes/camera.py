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


def generate_photo_id() -> str:
    """Generate a unique photo ID."""
    return f"photo_{uuid.uuid4().hex}"


def pil_to_base64(image_bytes: bytes) -> str:
    """Convert PIL image bytes to base64 string."""
    import base64
    return f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"


async def apply_frame_from_bytes(photo_data: bytes, frame_data: bytes) -> bytes:
    """Apply frame to photo from bytes and return as bytes.

    Uses only Pillow (PIL) - no OpenCV needed.
    """
    from PIL import Image

    # Load photo from bytes (supports JPEG, PNG, WebP)
    photo_pil = Image.open(io.BytesIO(photo_data))

    # Convert photo to RGBA if it isn't already
    if photo_pil.mode != 'RGBA':
        photo_pil = photo_pil.convert('RGBA')

    # Load frame from bytes
    frame = Image.open(io.BytesIO(frame_data))
    if frame.mode != 'RGBA':
        frame = frame.convert('RGBA')

    # Get dimensions
    photo_width, photo_height = photo_pil.size
    frame_width, frame_height = frame.size

    # Calculate scaling to cover photo completely
    scale_x = photo_width / frame_width
    scale_y = photo_height / frame_height
    scale = max(scale_x, scale_y)

    # Scale frame to cover photo
    scaled_frame_width = int(frame_width * scale)
    scaled_frame_height = int(frame_height * scale)
    frame_scaled = frame.resize((scaled_frame_width, scaled_frame_height), Image.Resampling.LANCZOS)

    # Crop frame to match photo dimensions (center crop)
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

    # Center photo on canvas
    photo_x = (photo_width - final_photo_width) // 2
    photo_y = (photo_height - final_photo_height) // 2

    # Create composition with photo as base
    composed = Image.new("RGBA", (photo_width, photo_height))
    composed.paste(photo_scaled, (photo_x, photo_y))

    # Composite frame on top using alpha blending
    composed_with_frame = Image.alpha_composite(composed, frame_cropped)

    # Convert to RGB for JPEG compatibility
    final = composed_with_frame.convert("RGB")

    # Convert to bytes
    img_bytes = io.BytesIO()
    final.save(img_bytes, format='PNG', quality=settings.PHOTO_QUALITY)
    return img_bytes.getvalue()


# Routes
@router.post("", response_model=CaptureResponse)
async def capture_photo(
    photo: UploadFile = File(...),
    frame_url: str = Form(...),
    frame_index: int = Form(...),
    session_id: str = Form(...),
    user: dict = Depends(get_current_user)
):
    """
    Capture a photo and apply the specified frame overlay.

    Args:
        photo: Uploaded photo file
        frame_url: URL of the frame to apply (can be data URL for custom frames)
        frame_index: Index of the frame (for logging purposes)
        session_id: Session identifier for temporary storage (not used on serverless)

    Returns:
        CaptureResponse with framed photo as base64

    Raises:
        HTTPException: If processing fails
    """
    import httpx
    import base64

    # Read photo data
    photo_data = await photo.read()

    # Validate file size
    max_size = settings.MAX_PHOTO_SIZE_MB * 1024 * 1024
    if len(photo_data) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Photo too large. Maximum size: {settings.MAX_PHOTO_SIZE_MB}MB"
        )

    # Get frame data from URL
    try:
        # Check if it's a data URL (custom frame from localStorage)
        if frame_url.startswith('data:'):
            # Extract base64 data from data URL
            # Format: data:image/png;base64,iVBORw0KGgo...
            header, encoded = frame_url.split(',', 1)
            frame_data = base64.b64decode(encoded)
            frame_id = f"custom_{frame_index}"
        else:
            # It's a regular URL, fetch from server
            async with httpx.AsyncClient(timeout=10.0) as client:
                frame_response = await client.get(frame_url)
                frame_response.raise_for_status()
                frame_data = frame_response.content
            # Extract frame ID from URL
            frame_id = frame_url.split('/')[-1].split('.')[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch frame: {str(e)}"
        )

    # Apply frame directly from bytes
    try:
        framed_photo_bytes = await apply_frame_from_bytes(photo_data, frame_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply frame: {str(e)}"
        )

    photo_id = generate_photo_id()

    return CaptureResponse(
        photo_id=photo_id,
        framed_photo=pil_to_base64(framed_photo_bytes),
        frame_used=frame_id
    )
