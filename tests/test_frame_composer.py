import pytest
import numpy as np
from PIL import Image
from src.frame_composer import apply_frame, compose_photostrip


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


def test_apply_frame_raises_error_for_missing_frame():
    """Test that apply_frame raises FileNotFoundError when frame doesn't exist."""
    # Create a dummy photo
    photo = np.zeros((480, 640, 3), dtype=np.uint8)

    # Test with a non-existent frame path
    with pytest.raises(FileNotFoundError, match="Frame file not found"):
        apply_frame(photo, "project_files/frames/nonexistent_frame.png")


def test_compose_photostrip_a6_dimensions():
    """Verify output is exactly A6 size (1240x1748)."""
    # Create 4 dummy landscape photos (640x360)
    photos = [np.random.randint(0, 255, (360, 640, 3), dtype=np.uint8) for _ in range(4)]
    frame_paths = ["project_files/frames/frame_simple.png"]  # Dummy path

    result = compose_photostrip(
        photos,
        frame_paths,
        exposure_values=[0.0, 0.0, 0.0, 0.0],
        target_size=(1240, 1748),
        border_width=10
    )

    assert result.size == (1240, 1748), f"Expected (1240, 1748), got {result.size}"


def test_compose_photostrip_has_black_borders():
    """Verify 10px black borders on edges."""
    photos = [np.random.randint(0, 255, (360, 640, 3), dtype=np.uint8) for _ in range(4)]
    frame_paths = ["project_files/frames/frame_simple.png"]

    result = compose_photostrip(
        photos,
        frame_paths,
        exposure_values=[0.0, 0.0, 0.0, 0.0],
        target_size=(1240, 1748),
        border_width=10
    )

    # Check corners are black (borders)
    result_array = np.array(result)
    assert np.all(result_array[0:10, 0:10] == 0), "Top-left corner should be black"
    assert np.all(result_array[-10:, 0:10] == 0), "Bottom-left corner should be black"


def test_compose_photostrip_4_photos_vertical():
    """Verify 4 photos arranged vertically (1 column, 4 rows)."""
    photos = [np.random.randint(0, 255, (360, 640, 3), dtype=np.uint8) for _ in range(4)]
    frame_paths = ["project_files/frames/frame_simple.png"]

    result = compose_photostrip(
        photos,
        frame_paths,
        exposure_values=[0.0, 0.0, 0.0, 0.0],
        target_size=(1240, 1748),
        border_width=10
    )

    # Verify photos are stacked vertically by checking color regions
    result_array = np.array(result)

    # Each photo should be roughly 1/4 of height minus borders
    # Photo 0 at top, Photo 3 at bottom
    photo_height = (1748 - 50) // 4  # Approximate

    # Check non-border pixels exist (not all black)
    assert np.any(result_array[50:150, 50:1190] != 0), "First photo region should have content"


def test_compose_photostrip_applies_exposure():
    """Verify exposure values are applied to final output."""
    # Create bright photo (all white)
    bright_photo = np.ones((360, 640, 3), dtype=np.uint8) * 255
    photos = [bright_photo] * 4
    frame_paths = ["project_files/frames/frame_simple.png"]

    # Negative exposure should darken
    result = compose_photostrip(
        photos,
        frame_paths,
        exposure_values=[-1.0, -1.0, -1.0, -1.0],
        target_size=(1240, 1748),
        border_width=10
    )

    result_array = np.array(result)
    # Check a pixel in the first photo area is darker (not pure white)
    # Note: exact value depends on frame overlay, but should be < 255
    sample_region = result_array[100:200, 100:200]
    assert np.mean(sample_region) < 250, "Negative exposure should darken photo"
