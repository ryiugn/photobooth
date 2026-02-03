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
    photos: List[str]  # List of 4 or 9 base64-encoded framed photos
    frame_ids: List[str] | None = None  # Optional, not used (photos already framed)
    exposure_values: List[float] | None = None  # Exposure values for each photo [-2.0, +2.0]


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


def apply_exposure_to_image(image_bytes: bytes, exposure_value: float) -> bytes:
    """
    Apply exposure adjustment to an image.

    Args:
        image_bytes: Image data as bytes
        exposure_value: Exposure value in range [-2.0, +2.0]

    Returns:
        Adjusted image as bytes
    """
    from PIL import Image, ImageEnhance
    import numpy as np

    # Clamp exposure to valid range
    exposure_value = max(-2.0, min(2.0, exposure_value))

    # Load image
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # If no adjustment, return original
    if exposure_value == 0.0:
        return image_bytes

    # Calculate brightness factor: 2^exposure_value
    brightness_factor = 2.0 ** exposure_value

    # Apply brightness adjustment
    enhancer = ImageEnhance.Brightness(img)
    adjusted = enhancer.enhance(brightness_factor)

    # Convert to bytes
    output = io.BytesIO()
    adjusted.save(output, format='PNG')
    return output.getvalue()


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
    Compose multiple photos into a photostrip with frame overlays.

    For 4 photos: 2x2 grid
    For 9 photos: 3x3 grid

    Args:
        photo_bytes_list: List of photo data as bytes
        frame_bytes_list: List of frame data as bytes (one per photo)
        gap: Gap between photos in pixels

    Returns:
        Composed photostrip as bytes
    """
    from PIL import Image

    if len(photo_bytes_list) not in (4, 9) or len(frame_bytes_list) != len(photo_bytes_list):
        raise ValueError("Must have 4 or 9 photos and matching number of frames")

    photo_count = len(photo_bytes_list)

    # Determine grid layout
    if photo_count == 4:
        grid_cols = 2
        grid_rows = 2
    else:  # 9 photos
        grid_cols = 3
        grid_rows = 3

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

    # Use square photo size for grid
    photo_size = min(first_width, first_height)
    strip_width = (photo_size * grid_cols) + (gap * (grid_cols + 1))
    strip_height = (photo_size * grid_rows) + (gap * (grid_rows + 1))

    # Create strip image with white background
    photostrip = Image.new("RGB", (strip_width, strip_height), color=(255, 255, 255))

    # Paste each photo in grid layout
    for index, framed_photo in enumerate(framed_photos):
        col = index % grid_cols
        row = index // grid_cols

        # Resize photo to fit grid cell
        resized_photo = framed_photo.resize((photo_size, photo_size), Image.Resampling.BILINEAR)

        # Calculate position
        x = gap + (photo_size + gap) * col
        y = gap + (photo_size + gap) * row

        photostrip.paste(resized_photo, (x, y))

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
    Compose 4 or 9 already-framed photos into an A6 photostrip with black borders.

    Note: Photos are already framed by the capture endpoint.
    This endpoint stitches them together with optional exposure adjustments.

    Args:
        request: Composition request with 4 or 9 base64-encoded framed photos
                 and optional exposure values

    Returns:
        ComposeResponse with photostrip as base64

    Raises:
        HTTPException: If composition fails
    """
    # Validate photo count (4 or 9)
    photo_count = len(request.photos)
    if photo_count not in (4, 9):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Must provide exactly 4 or 9 photos, got {photo_count}"
        )

    # Initialize exposure values if not provided
    exposure_values = request.exposure_values if request.exposure_values else [0.0] * photo_count
    if len(exposure_values) != photo_count:
        exposure_values = (exposure_values + [0.0] * photo_count)[:photo_count]

    # Convert base64 photos to bytes and apply exposure
    try:
        photo_bytes_list = []
        for i, photo in enumerate(request.photos):
            photo_bytes = base64_to_bytes(photo)
            # Apply exposure if not zero
            if exposure_values[i] != 0.0:
                photo_bytes = apply_exposure_to_image(photo_bytes, exposure_values[i])
            photo_bytes_list.append(photo_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid photo data: {str(e)}"
        )

    # Stitch the framed photos together with A6 layout
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


async def stitch_photostrip_from_bytes(photo_bytes_list: List[bytes], gap: int = 10) -> bytes:
    """
    Stitch already-framed photos into an A6 photostrip with black borders.

    For 4 photos: vertical strip (1 column × 4 rows)
    For 9 photos: 3×3 grid

    Args:
        photo_bytes_list: List of 4 or 9 framed photos as bytes
        gap: Gap between photos in pixels (border width)

    Returns:
        Composed photostrip as bytes
    """
    from PIL import Image

    photo_count = len(photo_bytes_list)
    if photo_count not in (4, 9):
        raise ValueError(f"Must have exactly 4 or 9 photos, got {photo_count}")

    # A6 dimensions at 150 DPI
    target_width = 1240
    target_height = 1748
    border_width = gap

    # Determine grid layout
    if photo_count == 4:
        grid_cols = 1
        grid_rows = 4
    else:  # 9 photos
        grid_cols = 3
        grid_rows = 3

    # Load each framed photo
    framed_photos = []
    for photo_bytes in photo_bytes_list:
        photo_pil = Image.open(io.BytesIO(photo_bytes))
        # Convert to RGB if needed
        if photo_pil.mode != 'RGB':
            photo_pil = photo_pil.convert('RGB')
        framed_photos.append(photo_pil)

    # Calculate photo dimensions to fit A6 with borders
    # Available space = total size - (border_width * (grid_dim + 1))
    available_width = target_width - (border_width * (grid_cols + 1))
    available_height = target_height - (border_width * (grid_rows + 1))

    photo_width = available_width // grid_cols
    photo_height = available_height // grid_rows

    # Resize all photos to calculated dimensions
    resized_photos = []
    for framed_photo in framed_photos:
        resized = framed_photo.resize((photo_width, photo_height), Image.Resampling.LANCZOS)
        resized_photos.append(resized)

    # Create A6 canvas with black background (creates outer borders)
    photostrip = Image.new("RGB", (target_width, target_height), color=(0, 0, 0))

    # Paste each photo in grid layout with borders
    for index, resized_photo in enumerate(resized_photos):
        col = index % grid_cols
        row = index // grid_cols

        # Calculate position with border offset
        x = border_width + (col * (photo_width + border_width))
        y = border_width + (row * (photo_height + border_width))

        photostrip.paste(resized_photo, (x, y))

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
