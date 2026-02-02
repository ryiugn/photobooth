import numpy as np
from PIL import Image
from pathlib import Path
import cv2


def compose_photostrip(photos: list, frame_paths, gap: int = 20) -> Image.Image:
    """
    Compose multiple photos into a photostrip with frame overlay.

    Layouts:
    - 4 photos: vertical strip (2x2 grid or 1x4 vertical)
    - 9 photos: 3x3 grid

    Args:
        photos: List of captured photos as numpy arrays (BGR format from OpenCV)
        frame_paths: Path to frame PNG file (str) or list of paths (one per photo)
        gap: Gap between photos in pixels (default: 20)

    Returns:
        Composed PIL Image with all photos arranged and frame applied to each

    Raises:
        FileNotFoundError: If frame file doesn't exist
        ValueError: If photos list is empty or not 4 or 9
    """
    if not photos:
        raise ValueError("No photos provided for composition")

    num_photos = len(photos)

    # Handle both single frame path (str) and multiple frame paths (list)
    if isinstance(frame_paths, str):
        # Single frame for all photos
        if not Path(frame_paths).exists():
            raise FileNotFoundError(f"Frame file not found: {frame_paths}")
        frame_paths_list = [frame_paths] * num_photos
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

    # Determine layout based on number of photos
    if num_photos == 4:
        # 4 photos: 2x2 grid layout (more compact than vertical)
        cols = 2
        rows = 2
    elif num_photos == 9:
        # 9 photos: 3x3 grid layout
        cols = 3
        rows = 3
    else:
        # Fallback: vertical strip (1 column, N rows)
        cols = 1
        rows = num_photos

    # Calculate strip dimensions
    strip_width = (first_width * cols) + (gap * (cols - 1))
    strip_height = (first_height * rows) + (gap * (rows - 1))

    # Create new image for the strip
    photostrip = Image.new("RGB", (strip_width, strip_height))

    # Paste each photo in grid layout
    for i, framed_photo in enumerate(framed_photos):
        row = i // cols
        col = i % cols
        x_offset = col * (first_width + gap)
        y_offset = row * (first_height + gap)
        photostrip.paste(framed_photo, (x_offset, y_offset))

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
    frame_scaled = frame.resize((scaled_frame_width, scaled_frame_height), Image.Resampling.BILINEAR)

    # Crop the scaled frame to match photo dimensions exactly (centered)
    crop_x = (scaled_frame_width - photo_width) // 2
    crop_y = (scaled_frame_height - photo_height) // 2
    frame_cropped = frame_scaled.crop((crop_x, crop_y, crop_x + photo_width, crop_y + photo_height))

    # Scale photo to COVER the entire area (not fit inside)
    # This ensures the photo fills the space behind the frame completely
    photo_scale_x = photo_width / rgb_photo.width
    photo_scale_y = photo_height / rgb_photo.height
    photo_scale = max(photo_scale_x, photo_scale_y)  # Use larger scale to cover entire area

    # Scale photo to cover
    final_photo_width = int(rgb_photo.width * photo_scale)
    final_photo_height = int(rgb_photo.height * photo_scale)
    photo_scaled = rgb_photo.resize((final_photo_width, final_photo_height), Image.Resampling.BILINEAR)

    # Create a white background for the frame (to make semi-transparent areas opaque)
    frame_with_opaque_bg = Image.new("RGBA", frame_cropped.size, (255, 255, 255, 255))

    # Paste the frame onto the white background, but ONLY keep fully transparent areas as holes
    # Pixels with alpha < 128 are considered "cutout" (transparent)
    # Pixels with alpha >= 128 become fully opaque
    frame_data = frame_cropped.load()
    opaque_data = frame_with_opaque_bg.load()

    for y in range(frame_cropped.size[1]):
        for x in range(frame_cropped.size[0]):
            r, g, b, a = frame_data[x, y]
            if a < 128:
                # This is the cutout area - keep it fully transparent
                opaque_data[x, y] = (255, 255, 255, 0)
            else:
                # This is the frame - make it fully opaque
                opaque_data[x, y] = (r, g, b, 255)

    frame_cropped = frame_with_opaque_bg

    # Center the photo (crop will happen if aspect ratios differ)
    photo_x = (photo_width - final_photo_width) // 2
    photo_y = (photo_height - final_photo_height) // 2

    # Create a new image for composition (RGB with white background)
    composed = Image.new("RGB", (photo_width, photo_height), (255, 255, 255))

    # Paste scaled photo (centered, may extend beyond edges which is fine)
    composed.paste(photo_scaled, (photo_x, photo_y))

    # Convert composed to RGBA for frame overlay
    composed_rgba = composed.convert("RGBA")

    # Paste cropped frame on top (using alpha channel for transparency)
    composed_rgba.paste(frame_cropped, (0, 0), frame_cropped)

    # Convert back to RGB for saving
    return composed_rgba.convert("RGB")


def cv2_to_rgb(bgr_image: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR numpy array to PIL RGB Image."""
    # Convert BGR to RGB
    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    # Convert to PIL Image
    return Image.fromarray(rgb)
