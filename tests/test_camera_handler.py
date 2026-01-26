import pytest
import numpy as np
from PyQt5.QtWidgets import QApplication
import sys
from src.camera_handler import CameraHandler

@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for PyQt5 tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't delete the QApplication, as it may be used by other tests

def test_camera_handler_initialization():
    handler = CameraHandler(device_index=0)
    assert handler.camera is not None
    handler.release()

def test_capture_photo():
    handler = CameraHandler(device_index=0)
    photo = handler.capture_photo()
    assert isinstance(photo, np.ndarray)
    assert photo.shape[2] == 3  # BGR color image
    handler.release()

def test_get_frame_returns_qpixmap(qapp):
    from PyQt5.QtGui import QPixmap
    handler = CameraHandler(device_index=0)
    pixmap = handler.get_frame()
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()
    handler.release()
