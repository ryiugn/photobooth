import numpy as np
from PIL import Image
from pathlib import Path
import cv2


def compose_photostrip(
    photos: list,
    frame_paths,
    exposure_values: list[float] = None,
    target_size: tuple = (1240, 1748),
    border_width: int = 10
) -> Image.Image:
    """
    Compose multiple photos into an A6 photostrip with frame overlay and black borders.

    Layouts:
    - 4 photos: vertical strip (1 column × 4 rows)
    - 9 photos: 3×3 grid

    Args:
        photos: List of captured photos as numpy arrays (BGR format from OpenCV)
        frame_paths: Path to frame PNG file (str) or list of paths (one per photo)
        exposure_values: Optional list of exposure adjustment values, one per photo.
                        Each value in range [-2.0, +2.0], None or 0.0 = no adjustment.
        target_size: Output dimensions as (width, height). Default A6 at 150 DPI: (1240, 1748)
        border_width: Width of black borders in pixels. Applied between photos and outer edges.

    Returns:
        Composed PIL Image with all photos arranged, frames applied, and black borders

    Raises:
        FileNotFoundError: If frame file doesn't exist
        ValueError: If photos list is empty
    """
    if not photos:
        raise ValueError("No photos provided for composition")

    num_photos = len(photos)
    target_width, target_height = target_size

    # Initialize exposure values if not provided
    if exposure_values is None:
        exposure_values = [0.0] * num_photos

    # Ensure exposure_values matches photos count
    if len(exposure_values) != num_photos:
        exposure_values = [exposure_values[i] if i < len(exposure_values) else 0.0
                          for i in range(num_photos)]

    # Import exposure utility
    from src.exposure_utils import apply_exposure

    # Handle both single frame path (str) and multiple frame paths (list)
    if isinstance(frame_paths, str):
        if not Path(frame_paths).exists():
            raise FileNotFoundError(f"Frame file not found: {frame_paths}")
        frame_paths_list = [frame_paths] * num_photos
    else:
        frame_paths_list = frame_paths
        for frame_path in frame_paths_list:
            if not Path(frame_path).exists():
                raise FileNotFoundError(f"Frame file not found: {frame_path}")

    # Apply exposure and convert all photos to PIL Images with frame applied
    framed_photos = []
    for i, (photo, frame_path) in enumerate(zip(photos, frame_paths_list)):
        # Apply exposure adjustment first
        adjusted_photo = photo
        if exposure_values[i] != 0.0:
            adjusted_photo = apply_exposure(photo, exposure_values[i])

        # Apply frame to each photo
        framed = apply_frame(adjusted_photo, frame_path)
        framed_photos.append(framed)

    # Determine layout based on number of photos
    if num_photos == 4:
        # 4 photos: vertical strip (1 column, 4 rows)
        cols = 1
        rows = 4
    elif num_photos == 9:
        # 9 photos: 3×3 grid layout
        cols = 3
        rows = 3
    else:
        # Fallback: calculate grid from photo count
        cols = 1
        rows = num_photos

    # Calculate photo dimensions to fit A6 with borders
    # Total horizontal space: (photo_width * cols) + (border_width * (cols + 1))
    # Total vertical space: (photo_height * rows) + (border_width * (rows + 1))
    available_width = target_width - (border_width * (cols + 1))
    available_height = target_height - (border_width * (rows + 1))

    photo_width = available_width // cols
    photo_height = available_height // rows

    # Resize all framed photos to calculated dimensions
    resized_photos = []
    for framed_photo in framed_photos:
        resized = framed_photo.resize((photo_width, photo_height), Image.Resampling.LANCZOS)
        resized_photos.append(resized)

    # Create A6 canvas with black background (creates outer borders)
    photostrip = Image.new("RGB", (target_width, target_height), (0, 0, 0))

    # Paste each photo in grid layout with borders
    for i, resized_photo in enumerate(resized_photos):
        row = i // cols
        col = i % cols

        # Calculate position with border offset
        x_offset = border_width + (col * (photo_width + border_width))
        y_offset = border_width + (row * (photo_height + border_width))

        photostrip.paste(resized_photo, (x_offset, y_offset))

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

    # Detect the dark "camera view" area and make everything else opaque
    # This works even if the frame has no transparency - it finds dark center regions
    import numpy as np

    # Convert frame to numpy array for processing
    frame_array = np.array(frame_cropped)

    # Calculate brightness of each pixel (using RGB values, ignoring alpha)
    # Brightness = (R + G + B) / 3
    if frame_array.shape[2] == 4:  # RGBA
        brightness = np.mean(frame_array[:, :, :3], axis=2)
    else:  # RGB
        brightness = np.mean(frame_array[:, :, :3], axis=2)

    # Find dark pixels (brightness threshold: below 80 out of 255)
    # This captures the dark "camera view" area
    dark_threshold = 80
    dark_mask = brightness < dark_threshold

    # Find connected components to identify the main dark region
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
        # (within 60% of the image dimensions from center)
        max_distance = min(frame_array.shape[0], frame_array.shape[1]) * 0.6
        center_proximity_mask = distances < max_distance

        # Combine: main dark region AND near center
        final_dark_mask = main_dark_mask & center_proximity_mask

        # Create the opaque frame
        frame_with_opaque_bg = np.array(frame_cropped.copy())

        # Set alpha channel: transparent for dark center, opaque everywhere else
        if frame_with_opaque_bg.shape[2] == 4:  # RGBA
            # Dark areas become transparent (alpha = 0)
            frame_with_opaque_bg[final_dark_mask, 3] = 0
            # Everything else becomes opaque (alpha = 255)
            frame_with_opaque_bg[~final_dark_mask, 3] = 255

        frame_cropped = Image.fromarray(frame_with_opaque_bg, mode='RGBA')
    else:
        # No dark regions found - fall back to original transparency behavior
        frame_with_opaque_bg = Image.new("RGBA", frame_cropped.size, (255, 255, 255, 255))
        frame_data = frame_cropped.load()
        opaque_data = frame_with_opaque_bg.load()

        for y in range(frame_cropped.size[1]):
            for x in range(frame_cropped.size[0]):
                r, g, b, a = frame_data[x, y]
                if a < 128:
                    opaque_data[x, y] = (255, 255, 255, 0)
                else:
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
