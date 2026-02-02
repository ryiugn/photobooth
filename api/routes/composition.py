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
from routes.auth import get_current_user

router = APIRouter()


# Request/Response Models
class ComposeRequest(BaseModel):
    """Request to compose photostrip from already-framed photos."""
    photos: List[str]  # List of 4 base64-encoded framed photos
    frame_ids: List[str] | None = None  # Optional, not used (photos already framed)


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

    Automatically detects dark "camera view" area in center of frame
    and makes everything else opaque.

    Args:
        photo_pil: PIL Image of the photo
        frame_pil: PIL Image of the frame (RGBA or RGB)

    Returns:
        PIL Image with frame applied
    """
    import numpy as np

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
    frame_scaled = frame_pil.resize((scaled_frame_width, scaled_frame_height), Image.Resampling.BILINEAR)

    # Crop frame to match photo dimensions (center crop)
    crop_x = (scaled_frame_width - photo_width) // 2
    crop_y = (scaled_frame_height - photo_height) // 2
    frame_cropped = frame_scaled.crop((crop_x, crop_y, crop_x + photo_width, crop_y + photo_height))

    # Detect the dark "camera view" area and make everything else opaque
    # Convert frame to numpy array for processing
    frame_array = np.array(frame_cropped)

    # Calculate brightness of each pixel
    if frame_array.shape[2] == 4:  # RGBA
        brightness = np.mean(frame_array[:, :, :3], axis=2)
    else:  # RGB
        brightness = np.mean(frame_array[:, :, :3], axis=2)

    # Find dark pixels (brightness threshold: below 80 out of 255)
    dark_threshold = 80
    dark_mask = brightness < dark_threshold

    # Find connected components to identify the main dark region
    try:
        from scipy import ndimage
        labeled, num_features = ndimage.label(dark_mask)

        if num_features > 0:
            # Find the largest dark region (likely the camera view)
            sizes = ndimage.sum(dark_mask, labeled, range(num_features + 1))
            largest_region = np.argmax(sizes[1:]) + 1  # Skip background (0)

            # Create mask for only the largest dark region
            main_dark_mask = (labeled == largest_region)

            # Additionally, prefer regions near the center (camera view is typically centered)
            center_y, center_x = frame_array.shape[0] // 2, frame_array.shape[1] // 2
            y_coords, x_coords = np.indices(frame_array.shape[:2])

            # Calculate distance from center for each dark pixel
            distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)

            # Only keep dark regions that are reasonably close to center
            max_distance = min(frame_array.shape[0], frame_array.shape[1]) * 0.6
            center_proximity_mask = distances < max_distance

            # Combine: main dark region AND near center
            final_dark_mask = main_dark_mask & center_proximity_mask

            # Create the opaque frame
            frame_with_opaque_bg = frame_array.copy()

            # Set alpha channel: transparent for dark center, opaque everywhere else
            if frame_with_opaque_bg.shape[2] == 4:  # RGBA
                # Dark areas become transparent (alpha = 0)
                frame_with_opaque_bg[final_dark_mask, 3] = 0
                # Everything else becomes opaque (alpha = 255)
                frame_with_opaque_bg[~final_dark_mask, 3] = 255

            frame_cropped = Image.fromarray(frame_with_opaque_bg, mode='RGBA')
    except ImportError:
        # scipy not available - fall back to simple center-based detection
        pass

    # Scale photo to fit within frame (contain)
    photo_scale_x = photo_width / photo_pil.width
    photo_scale_y = photo_height / photo_pil.height
    photo_scale = min(photo_scale_x, photo_scale_y)

    final_photo_width = int(photo_pil.width * photo_scale)
    final_photo_height = int(photo_pil.height * photo_scale)
    photo_scaled = photo_pil.resize((final_photo_width, final_photo_height), Image.Resampling.BILINEAR)

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
    user: dict = Depends(get_current_user)
):
    """
    Compose 4 already-framed photos into a vertical photostrip.

    Note: Photos are already framed by the capture endpoint.
    This endpoint only stitches them together.

    Args:
        request: Composition request with 4 base64-encoded framed photos

    Returns:
        ComposeResponse with photostrip as base64

    Raises:
        HTTPException: If composition fails
    """
    # Validate exactly 4 photos
    if len(request.photos) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide exactly 4 photos"
        )

    # Convert base64 photos to bytes
    try:
        photo_bytes_list = [base64_to_bytes(photo) for photo in request.photos]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid photo data: {str(e)}"
        )

    # Just stitch the already-framed photos together
    try:
        strip_bytes = await stitch_photostrip_from_bytes(photo_bytes_list)
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


async def stitch_photostrip_from_bytes(photo_bytes_list: List[bytes], gap: int = 20) -> bytes:
    """
    Stitch already-framed photos into a vertical photostrip.

    Args:
        photo_bytes_list: List of 4 framed photos as bytes
        gap: Gap between photos in pixels

    Returns:
        Composed photostrip as bytes
    """
    from PIL import Image

    if len(photo_bytes_list) != 4:
        raise ValueError("Must have exactly 4 photos")

    # Load each framed photo
    framed_photos = []
    for photo_bytes in photo_bytes_list:
        photo_pil = Image.open(io.BytesIO(photo_bytes))
        # Convert to RGB if needed
        if photo_pil.mode != 'RGB':
            photo_pil = photo_pil.convert('RGB')
        framed_photos.append(photo_pil)

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
