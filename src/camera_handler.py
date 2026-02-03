import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


class CameraHandler:
    """Manages camera operations for photobooth application."""

    def __init__(self, device_index: int = 0, width: int = 1280, height: int = 720):
        """Initialize camera with specified device and resolution."""
        self.device_index = device_index
        self.width = width
        self.height = height
        self.camera = cv2.VideoCapture(device_index)
        if not self.camera.isOpened():
            raise RuntimeError(f"Could not open camera at index {device_index}")
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def get_frame(self) -> QPixmap:
        """Capture a frame and return as QPixmap for display."""
        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError("Failed to capture frame from camera")

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert to QImage
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # Convert to QPixmap
        return QPixmap.fromImage(qt_image)

    def get_raw_frame(self) -> tuple:
        """Get raw camera frame as numpy array without conversion.

        Returns:
            Tuple of (ret, frame) where ret is bool success indicator
            and frame is numpy array in BGR format
        """
        ret, frame = self.camera.read()
        return ret, frame

    def capture_photo(self, target_width: int = None, target_height: int = None) -> np.ndarray:
        """Capture a single photo as numpy array (BGR format).

        Args:
            target_width: Optional target width to match preview display
            target_height: Optional target height to match preview display
                          If provided, the photo will be cropped to center to match preview

        Returns:
            Captured photo as numpy array (BGR format)
        """
        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError("Failed to capture photo from camera")

        # If target dimensions provided, crop to match preview (what user sees)
        if target_width and target_height:
            h, w = frame.shape[:2]

            # Calculate scaling to cover target area (same as Qt.KeepAspectRatio scaling)
            scale_x = target_width / w
            scale_y = target_height / h
            scale = max(scale_x, scale_y)

            # Scale frame to cover target dimensions
            scaled_w = int(w * scale)
            scaled_h = int(h * scale)
            frame_scaled = cv2.resize(frame, (scaled_w, scaled_h), interpolation=cv2.INTER_LINEAR)

            # Crop to center (same as preview display)
            crop_x = (scaled_w - target_width) // 2
            crop_y = (scaled_h - target_height) // 2
            frame_cropped = frame_scaled[crop_y:crop_y + target_height, crop_x:crop_x + target_width]

            print(f"[DEBUG] capture_photo: original=({w}x{h}), target=({target_width}x{target_height}), scaled=({scaled_w}x{scaled_h}), crop=({crop_x},{crop_y})")

            return frame_cropped

        return frame

    def release(self):
        """Release camera resources."""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
