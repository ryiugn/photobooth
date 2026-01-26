import pytest
from PyQt5.QtWidgets import QApplication
from src.pages.frame_selection import FrameSelectionPage

@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_frame_selection_loads_frames(app, qtbot):
    frames_dir = "project_files/frames"
    page = FrameSelectionPage(frames_dir=frames_dir)
    assert len(page.frames) > 0
    assert page.continue_button.isEnabled() == False

def test_selecting_frame_enables_continue(app, qtbot):
    page = FrameSelectionPage(frames_dir="project_files/frames")
    if len(page.frames) > 0:
        # Simulate frame selection
        page.select_frame(0)
        assert page.continue_button.isEnabled() == True
        assert page.selected_frame is not None
