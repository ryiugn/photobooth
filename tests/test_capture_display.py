import pytest
from PyQt5.QtWidgets import QApplication
from src.pages.capture_display import CaptureDisplayPage

@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_capture_display_initialization(app, qtbot):
    page = CaptureDisplayPage(frame_path="project_files/frames/frame_simple.png")
    assert page.frame_path == "project_files/frames/frame_simple.png"

def test_capture_photo_starts_camera(app, qtbot):
    page = CaptureDisplayPage(frame_path="project_files/frames/frame_simple.png")
    # Just test initialization, actual camera test needs hardware
    assert page.capture_button is not None
    assert page.save_button is not None
