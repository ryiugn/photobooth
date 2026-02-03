import numpy as np
import cv2


def apply_exposure(frame: np.ndarray, exposure_value: float) -> np.ndarray:
    """Apply exposure adjustment to a camera frame.

    Args:
        frame: Input frame as numpy array (BGR format from OpenCV)
        exposure_value: Exposure adjustment value in range [-2.0, +2.0]
                       -2.0 = 1/4 brightness (darken)
                       0.0 = no change
                       +2.0 = 4x brightness (brighten)

    Returns:
        Adjusted frame as numpy array (same dtype and shape as input)

    Raises:
        ValueError: If frame is empty or invalid
    """
    if frame is None or frame.size == 0:
        raise ValueError("Frame cannot be empty")

    # Clamp exposure to valid range
    exposure_value = max(-2.0, min(2.0, exposure_value))

    # If no adjustment, return original
    if exposure_value == 0.0:
        return frame

    # Calculate scaling factor: 2^exposure_value
    # -2.0 -> 0.25 (1/4 brightness)
    # -1.0 -> 0.5  (1/2 brightness)
    #  0.0 -> 1.0  (no change)
    # +1.0 -> 2.0  (2x brightness)
    # +2.0 -> 4.0  (4x brightness)
    alpha = 2.0 ** exposure_value

    # Apply brightness adjustment using OpenCV
    # convertScaleAbs: output = saturate_cast(alpha * input + beta)
    # We only use alpha (brightness multiplier), beta stays 0
    adjusted = cv2.convertScaleAbs(frame, alpha=alpha, beta=0)

    return adjusted
