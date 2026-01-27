import numpy as np
from PIL import Image
from pathlib import Path
import cv2


def compose_photostrip(photos: list, frame_paths, gap: int = 20) -> Image.Image:
    """
    Compose multiple photos into a vertical photostrip with frame overlay.

    Args:
        photos: List of captured photos as numpy arrays (BGR format from OpenCV)
        frame_paths: Path to frame PNG file (str) or list of paths (one per photo)
        gap: Gap between photos in pixels (default: 20)

    Returns:
        Composed PIL Image with all photos stacked vertically and frame applied to each

    Raises:
        FileNotFoundError: If frame file doesn't exist
        ValueError: If photos list is empty
    """
    if not photos:
        raise ValueError("No photos provided for composition")

    # Handle both single frame path (str) and multiple frame paths (list)
    if isinstance(frame_paths, str):
        # Single frame for all photos
        if not Path(frame_paths).exists():
            raise FileNotFoundError(f"Frame file not found: {frame_paths}")
        frame_paths_list = [frame_paths] * len(photos)
    else:
        # Multiple frames (one per photo)
        frame_paths_list = frame_paths
        for frame_path in frame_paths_list:
            if not Path(frame_path).exists():
                raise FileNotFoundError(f"Frame file not found: {frame_path}")

    # Convert all photos to PIL Images with frame applied
    framed_photos = []
    for photo, frame_path in zip(photos, frame_paths_list):
        # Apply frame to each photo
        framed = apply_frame(photo, frame_path)
        framed_photos.append(framed)

    # Get dimensions from first framed photo
    first_width, first_height = framed_photos[0].size

    # Calculate strip dimensions
    strip_width = first_width
    strip_height = (first_height * len(framed_photos)) + (gap * (len(framed_photos) - 1))

    # Create new image for the strip
    photostrip = Image.new("RGB", (strip_width, strip_height))

    # Paste each photo vertically
    y_offset = 0
    for framed_photo in framed_photos:
        photostrip.paste(framed_photo, (0, y_offset))
        y_offset += first_height + gap

    return photostrip


def apply_frame(photo: np.ndarray, frame_path: str) -> Image.Image:
    """
    Apply a frame overlay to a captured photo.

    The frame is cropped to fit the photo dimensions exactly.
    The photo is scaled to fit within the frame (maintaining aspect ratio).

    Args:
        photo: Captured photo as numpy array (BGR format from OpenCV)
        frame_path: Path to frame PNG file with transparency

    Returns:
        Composed PIL Image with frame overlay

    Raises:
        FileNotFoundError: If frame file doesn't exist
    """
    # Check if frame file exists
    frame_file = Path(frame_path)
    if not frame_file.exists():
        raise FileNotFoundError(f"Frame file not found: {frame_path}")

    # Convert BGR photo to RGB
    rgb_photo = cv2_to_rgb(photo)

    # Open the frame PNG
    frame = Image.open(frame_path).convert("RGBA")

    # Get dimensions
    photo_width, photo_height = rgb_photo.size
    frame_width, frame_height = frame.size

    # Calculate scaling to make frame cover the photo (crop frame if needed)
    scale_x = photo_width / frame_width
    scale_y = photo_height / frame_height
    scale = max(scale_x, scale_y)  # Use larger scale to cover entire photo

    # Scale frame to cover photo dimensions
    scaled_frame_width = int(frame_width * scale)
    scaled_frame_height = int(frame_height * scale)
    frame_scaled = frame.resize((scaled_frame_width, scaled_frame_height), Image.Resampling.LANCZOS)

    # Crop the scaled frame to match photo dimensions exactly (centered)
    crop_x = (scaled_frame_width - photo_width) // 2
    crop_y = (scaled_frame_height - photo_height) // 2
    frame_cropped = frame_scaled.crop((crop_x, crop_y, crop_x + photo_width, crop_y + photo_height))

    # Scale photo to fit within the frame's visible area (contain, not cover)
    # Calculate how much to scale the photo to fit inside
    photo_scale_x = photo_width / rgb_photo.width
    photo_scale_y = photo_height / rgb_photo.height
    photo_scale = min(photo_scale_x, photo_scale_y)  # Use smaller scale to fit inside

    # Scale photo to fit (contain within frame)
    final_photo_width = int(rgb_photo.width * photo_scale)
    final_photo_height = int(rgb_photo.height * photo_scale)
    photo_scaled = rgb_photo.resize((final_photo_width, final_photo_height), Image.Resampling.LANCZOS)

    # Center the photo
    photo_x = (photo_width - final_photo_width) // 2
    photo_y = (photo_height - final_photo_height) // 2

    # Create a new image for composition
    composed = Image.new("RGBA", (photo_width, photo_height))

    # Paste scaled photo (centered)
    composed.paste(photo_scaled, (photo_x, photo_y))

    # Paste cropped frame on top (using alpha channel for transparency)
    composed.paste(frame_cropped, (0, 0), frame_cropped)

    # Convert back to RGB for saving
    return composed.convert("RGB")


def cv2_to_rgb(bgr_image: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR numpy array to PIL RGB Image."""
    # Convert BGR to RGB
    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    # Convert to PIL Image
    return Image.fromarray(rgb)
