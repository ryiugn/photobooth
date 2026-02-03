import numpy as np
import cv2
from src.exposure_utils import apply_exposure

def test_exposure_zero_returns_original():
    """Exposure of 0.0 should return original image unchanged."""
    frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    result = apply_exposure(frame, 0.0)
    np.testing.assert_array_equal(result, frame)

def test_exposure_positive_increases_brightness():
    """Positive exposure should increase brightness."""
    frame = np.ones((100, 100, 3), dtype=np.uint8) * 128  # Mid-gray
    result = apply_exposure(frame, 1.0)  # 2x brightness
    # Result should be brighter (close to 255, not clipped)
    assert np.mean(result) > np.mean(frame)

def test_exposure_negative_decreases_brightness():
    """Negative exposure should decrease brightness."""
    frame = np.ones((100, 100, 3), dtype=np.uint8) * 128  # Mid-gray
    result = apply_exposure(frame, -1.0)  # 0.5x brightness
    # Result should be darker
    assert np.mean(result) < np.mean(frame)

def test_exposure_clamps_range():
    """Exposure should be clamped to [-2.0, +2.0]."""
    frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
    result_high = apply_exposure(frame, 5.0)  # Should clamp to 2.0
    result_low = apply_exposure(frame, -5.0)   # Should clamp to -2.0
    # Both should behave same as clamped values
    expected_high = apply_exposure(frame, 2.0)
    expected_low = apply_exposure(frame, -2.0)
    np.testing.assert_array_equal(result_high, expected_high)
    np.testing.assert_array_equal(result_low, expected_low)
