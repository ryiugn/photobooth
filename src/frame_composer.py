import numpy as np
from PIL import Image
import cv2


def apply_frame(photo: np.ndarray, frame_path: str) -> Image.Image:
    """
    Apply a frame overlay to a captured photo.

    Args:
        photo: Captured photo as numpy array (BGR format from OpenCV)
        frame_path: Path to frame PNG file with transparency

    Returns:
        Composed PIL Image with frame overlay
    """
    # Convert BGR photo to RGB
    rgb_photo = cv2_to_rgb(photo)

    # Open the frame PNG
    frame = Image.open(frame_path).convert("RGBA")

    # Get frame dimensions
    frame_width, frame_height = frame.size

    # Calculate photo dimensions to fit within frame
    # Assuming frame has a transparent center area
    # For simple frames, we'll resize photo to match frame
    photo_resized = rgb_photo.resize((frame_width, frame_height), Image.Resampling.LANCZOS)

    # Create a new image for composition
    composed = Image.new("RGBA", (frame_width, frame_height))

    # Paste photo first
    composed.paste(photo_resized, (0, 0))

    # Paste frame on top (using alpha channel)
    composed.paste(frame, (0, 0), frame)

    # Convert back to RGB for saving
    return composed.convert("RGB")


def cv2_to_rgb(bgr_image: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR numpy array to PIL RGB Image."""
    # Convert BGR to RGB
    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    # Convert to PIL Image
    return Image.fromarray(rgb)
