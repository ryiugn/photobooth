"""
Photobooth Application - Main Entry Point

This is the main application that ties together all pages using QStackedWidget
for navigation. It manages the application lifecycle and page transitions.

Application Flow:
1. Login Screen (Page 0) - PIN authentication
2. Frame Selection (Page 1) - Choose photo frame
3. Photo Capture (Page 2) - Take photo with selected frame
4. Return to Frame Selection or Exit
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication, QStackedWidget
from PyQt5.QtCore import Qt
from src.pages.login import LoginPage
from src.pages.frame_selection import FrameSelectionPage
from src.pages.capture_display import CaptureDisplayPage


class PhotoboothApp(QStackedWidget):
    """
    Main photobooth application managing page navigation.

    This class:
    - Initializes all pages (Login, Frame Selection, Capture)
    - Manages page transitions based on user actions
    - Handles cleanup on exit
    - Connects signals between pages for navigation
    """

    def __init__(self):
        """Initialize the photobooth application."""
        super().__init__()

        # Dictionary to hold page references
        self.pages = {}

        # Setup pages, connect signals, and show maximized
        self.setup_pages()
        self.connect_signals()
        self.showMaximized()

        # Apply FOFOBOOTH styling
        self.setStyleSheet("background-color: #333333;")

    def setup_pages(self):
        """
        Initialize all pages and add to stacked widget.

        Creates:
        - Login page (Page 0) - Always created first
        - Frame Selection page (Page 1) - Created after login
        - Capture page (Page 2) - Created dynamically when frame is selected
        """
        # Load configuration for PIN and directories
        config = LoginPage.load_config()
        pin = config.get("pin", "1234")
        frames_dir = config.get("frames_dir", "project_files/frames")
        output_dir = config.get("output_dir", "project_files/captured_images")

        # Page 0: Login Screen
        self.pages["login"] = LoginPage(correct_pin=pin)
        self.addWidget(self.pages["login"])

        # Page 1: Frame Selection
        self.pages["frame_selection"] = FrameSelectionPage(frames_dir=frames_dir)
        self.addWidget(self.pages["frame_selection"])

        # Page 2: Capture & Display (created dynamically when frame is selected)
        self.pages["capture"] = None

        # Start at login page
        self.setCurrentWidget(self.pages["login"])

    def connect_signals(self):
        """
        Connect page signals for navigation flow.

        Signal connections:
        - Login.authenticated → go_to_frame_selection()
        - FrameSelection.frame_selected → go_to_capture(frame_path)
        - Capture.retake_requested → go_to_frame_selection()
        - Capture.photo_saved → on_photo_saved()
        """
        # Login → Frame Selection
        self.pages["login"].authenticated.connect(self.go_to_frame_selection)

        # Frame Selection → Capture
        self.pages["frame_selection"].frame_selected.connect(self.go_to_capture)

    def go_to_frame_selection(self):
        """
        Navigate to frame selection page.

        Called after successful authentication.
        """
        self.setCurrentWidget(self.pages["frame_selection"])

    def go_to_capture(self, frame_path: str):
        """
        Navigate to capture page with selected frame.

        Args:
            frame_path: Path to the selected frame image

        This method:
        1. Creates a new CaptureDisplayPage with the selected frame
        2. Cleans up the old capture page if it exists
        3. Connects signals for the new capture page
        4. Navigates to the capture page
        5. Initializes the camera
        """
        # Create capture page with selected frame
        output_dir = "project_files/captured_images"
        capture_page = CaptureDisplayPage(frame_path=frame_path, output_dir=output_dir)

        # Clean up old capture page if exists
        if self.pages["capture"] is not None:
            old_page = self.pages["capture"]
            old_page.cleanup()
            self.removeWidget(old_page)

        # Add new capture page
        self.pages["capture"] = capture_page
        self.addWidget(capture_page)

        # Connect signals
        capture_page.retake_requested.connect(self.go_to_frame_selection)
        capture_page.photo_saved.connect(self.on_photo_saved)

        # Navigate and initialize camera
        self.setCurrentWidget(capture_page)
        capture_page.initialize_camera()

    def on_photo_saved(self):
        """
        Handle photo saved event.

        This method:
        1. Cleans up the capture page (releases camera)
        2. Returns to frame selection for next session

        Called when user saves a photo.
        """
        # Return to frame selection for next session
        if self.pages["capture"]:
            self.pages["capture"].cleanup()
        self.setCurrentWidget(self.pages["frame_selection"])

    def keyPressEvent(self, event):
        """
        Handle key press events.

        Args:
            event: QKeyEvent

        Allows ESC key to exit the application.
        """
        # ESC to exit fullscreen
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """
        Cleanup on application close.

        Args:
            event: QCloseEvent

        Ensures camera resources are released before closing.
        """
        if self.pages.get("capture"):
            self.pages["capture"].cleanup()
        event.accept()


def main():
    """
    Main entry point for the application.

    Creates QApplication, PhotoboothApp window, and starts the event loop.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Photobooth")

    window = PhotoboothApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
