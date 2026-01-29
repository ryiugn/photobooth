"""
Composition routes for generating photostrips from multiple photos.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List
from pathlib import Path
import uuid
import io
import base64
from datetime import datetime

from config import settings
from routes.auth import get_current_user_dict

router = APIRouter()


# Request/Response Models
class ComposeRequest(BaseModel):
    """Request to compose photostrip."""
    photos: List[str]  # List of 4 base64-encoded photos
    frame_ids: List[str]  # List of 4 frame IDs


class ComposeResponse(BaseModel):
    """Response with composed photostrip."""
    strip_id: str
    photostrip_base64: str
    download_url: str


# Utility Functions
def generate_strip_id() -> str:
    """Generate a unique photostrip ID."""
    return f"strip_{uuid.uuid4().hex}"


def pil_to_base64(image_bytes: bytes) -> str:
    """Convert PIL image bytes to base64 string."""
    return f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"


def base64_to_bytes(base64_data: str) -> bytes:
    """Convert base64 string to bytes."""
    # Remove data URL prefix if present
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]
    return base64.b64decode(base64_data)


async def apply_frame_to_photo_pil(photo_pil, frame_pil):
    """
    Apply frame to photo using only Pillow.

    Args:
        photo_pil: PIL Image of the photo
        frame_pil: PIL Image of the frame (RGBA)

    Returns:
        PIL Image with frame applied
    """
    # Convert photo to RGBA if needed
    if photo_pil.mode != 'RGBA':
        photo_pil = photo_pil.convert('RGBA')

    # Convert frame to RGBA if needed
    if frame_pil.mode != 'RGBA':
        frame_pil = frame_pil.convert('RGBA')

    # Get dimensions
    photo_width, photo_height = photo_pil.size
    frame_width, frame_height = frame_pil.size

    # Calculate scaling to cover photo completely
    scale_x = photo_width / frame_width
    scale_y = photo_height / frame_height
    scale = max(scale_x, scale_y)

    # Scale frame to cover photo
    scaled_frame_width = int(frame_width * scale)
    scaled_frame_height = int(frame_height * scale)
    frame_scaled = frame_pil.resize((scaled_frame_width, scaled_frame_height), Image.Resampling.LANCZOS)

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

    # Convert to RGB
    final = composed_with_frame.convert("RGB")
    return final


async def compose_photostrip_from_bytes(photo_bytes_list: List[bytes], frame_bytes_list: List[bytes], gap: int = 20) -> bytes:
    """
    Compose multiple photos into a vertical photostrip with frame overlays.

    Args:
        photo_bytes_list: List of photo data as bytes
        frame_bytes_list: List of frame data as bytes (one per photo)
        gap: Gap between photos in pixels

    Returns:
        Composed photostrip as bytes
    """
    from PIL import Image

    if len(photo_bytes_list) != 4 or len(frame_bytes_list) != 4:
        raise ValueError("Must have exactly 4 photos and 4 frames")

    # Load and frame each photo
    framed_photos = []
    for photo_bytes, frame_bytes in zip(photo_bytes_list, frame_bytes_list):
        # Load photo from bytes
        photo_pil = Image.open(io.BytesIO(photo_bytes))

        # Load frame from bytes
        frame_pil = Image.open(io.BytesIO(frame_bytes))

        # Apply frame
        framed = await apply_frame_to_photo_pil(photo_pil, frame_pil)
        framed_photos.append(framed)

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


# Routes
@router.post("", response_model=ComposeResponse)
async def compose_photostrip(
    request: ComposeRequest,
    user: dict = Depends(get_current_user_dict)
):
    """
    Compose 4 captured photos into a vertical photostrip with frame overlays.

    Args:
        request: Composition request with photos and frame IDs

    Returns:
        ComposeResponse with photostrip as base64

    Raises:
        HTTPException: If composition fails
    """
    # Validate exactly 4 photos
    if len(request.photos) != 4 or len(request.frame_ids) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide exactly 4 photos and 4 frames"
        )

    # Convert base64 photos to bytes
    try:
        photo_bytes_list = [base64_to_bytes(photo) for photo in request.photos]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid photo data: {str(e)}"
        )

    # Fetch frame data from frontend
    import httpx

    frontend_url = settings.FRONTEND_URL.rstrip('/')
    all_frames = [
        {"id": "frame_simple", "filename": "frame_simple.png"},
        {"id": "frame_kawaii", "filename": "frame_kawaii.png"},
        {"id": "frame_classic", "filename": "frame_classic.png"},
        {"id": "custom_pwumpd", "filename": "custom_20260127_095644_pwumpd.webp"},
        {"id": "custom_lyazbf", "filename": "custom_20260127_204241_lyazbf.PNG"},
        {"id": "custom_egptpm", "filename": "custom_20260127_210302_egptpm.PNG"},
        {"id": "custom_hxgbqw", "filename": "custom_20260127_210302_hxgbqw.PNG"},
        {"id": "custom_ieyzow", "filename": "custom_20260127_210302_ieyzow.PNG"},
        {"id": "custom_jhmwdz", "filename": "custom_20260127_210302_jhmwdz.PNG"}
    ]

    # Create frame lookup
    frame_lookup = {f["id"]: f["filename"] for f in all_frames}

    # Fetch frame data for each frame ID
    frame_bytes_list = []
    for frame_id in request.frame_ids:
        if frame_id not in frame_lookup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Frame '{frame_id}' not found"
            )

        frame_url = f"{frontend_url}/frames/{frame_lookup[frame_id]}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                frame_response = await client.get(frame_url)
                frame_response.raise_for_status()
                frame_bytes_list.append(frame_response.content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch frame '{frame_id}': {str(e)}"
            )

    # Compose photostrip
    try:
        strip_bytes = await compose_photostrip_from_bytes(photo_bytes_list, frame_bytes_list)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compose photostrip: {str(e)}"
        )

    # Generate strip ID
    strip_id = generate_strip_id()

    return ComposeResponse(
        strip_id=strip_id,
        photostrip_base64=pil_to_base64(strip_bytes),
        download_url=f"/api/v1/composition/download/{strip_id}"
    )


@router.get("/download/{strip_id}")
async def download_photostrip(strip_id: str, user: dict = Depends(get_current_user)):
    """
    Download a completed photostrip.

    Note: On serverless platforms, photostrips are not persisted.
    This endpoint returns a placeholder response.

    Args:
        strip_id: Photostrip identifier

    Returns:
        Message indicating download limitation
    """
    return {
        "message": "Photostrip downloads are handled client-side on serverless platforms",
        "strip_id": strip_id
    }
