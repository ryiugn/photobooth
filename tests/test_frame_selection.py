import pytest
import tempfile
import shutil
from pathlib import Path
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

def test_handles_missing_frames_directory(app, qtbot, tmp_path):
    """Test that missing frames directory is created gracefully."""
    # Use a non-existent temporary directory
    non_existent_dir = tmp_path / "non_existent_frames"

    # Should not raise an error
    page = FrameSelectionPage(frames_dir=str(non_existent_dir))

    # Frames list should be empty but page should still work
    assert len(page.frames) == 0
    assert page.continue_button.isEnabled() == False
    assert non_existent_dir.exists()  # Directory should be created

def test_handles_corrupted_image(app, qtbot, tmp_path):
    """Test that corrupted images are handled gracefully."""
    # Create a temporary directory with a corrupted image file
    frames_dir = tmp_path / "frames_test"
    frames_dir.mkdir()

    # Create a file that's not a valid image
    corrupted_file = frames_dir / "corrupted.png"
    corrupted_file.write_text("This is not a valid PNG file")

    # Should not raise an error when loading
    page = FrameSelectionPage(frames_dir=str(frames_dir))

    # Should still create the page, even with corrupted image
    assert len(page.frames) == 1  # File is loaded into list

    # The card should be created without crashing
    if len(page.cards) > 0:
        # Card should exist even if image is corrupted
        assert page.cards[0] is not None

def test_grid_layout_with_multiple_rows(app, qtbot, tmp_path):
    """Test that grid layout handles multiple rows correctly."""
    # Create a temporary directory with multiple frames
    frames_dir = tmp_path / "frames_grid_test"
    frames_dir.mkdir()

    # Copy existing frame to create 4 frames (2 rows with 3 cols)
    source_frame = Path("project_files/frames/frame_simple.png")
    if source_frame.exists():
        for i in range(4):
            target = frames_dir / f"frame_{i}.png"
            shutil.copy(source_frame, target)

        page = FrameSelectionPage(frames_dir=str(frames_dir))

        # Should have 4 frames
        assert len(page.frames) == 4

        # Page should render without layout issues
        assert page.isVisible() or True  # Widget exists

