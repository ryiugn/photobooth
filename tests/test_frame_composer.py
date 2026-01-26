import pytest
import numpy as np
from PIL import Image
from src.frame_composer import apply_frame


def test_apply_frame_creates_composed_image():
    """Test that apply_frame creates a composed image with frame overlay."""
    # Create a dummy photo (RGB)
    photo = np.zeros((480, 640, 3), dtype=np.uint8)
    photo[:, :] = [100, 150, 200]  # Fill with a color

    # Test with the simple frame we created
    result = apply_frame(photo, "project_files/frames/frame_simple.png")

    # Verify the result is a PIL Image
    assert isinstance(result, Image.Image)

    # Verify dimensions match or exceed the photo dimensions
    assert result.width >= 640
    assert result.height >= 480

    # Verify the image is in RGB mode (not RGBA)
    assert result.mode == "RGB"
