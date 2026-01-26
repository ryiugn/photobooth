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

    def capture_photo(self) -> np.ndarray:
        """Capture a single photo as numpy array (BGR format)."""
        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError("Failed to capture photo from camera")
        return frame

    def release(self):
        """Release camera resources."""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
