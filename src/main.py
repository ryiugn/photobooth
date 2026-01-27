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
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QStackedWidget
from PyQt5.QtCore import Qt

# Change working directory to project root for relative paths to work
import os
os.chdir(project_root)

from src.pages.login import LoginPage
from src.pages.frame_selection import FrameSelectionPage
from src.pages.template_manager import TemplateManagerPage
from src.pages.capture_display import CaptureDisplayPage
from src.pages.photostrip_reveal import PhotostripRevealPage


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

        # Apply scallop seashell gradient background
        self.setStyleSheet("""
            QStackedWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFF8DC,
                    stop:0.3 #FFF0E0,
                    stop:0.6 #FFE4C4,
                    stop:1 #FFDAB9
                );
            }
        """)

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

        # Page 3: Photostrip Reveal (created dynamically when photo is captured)
        self.pages["photostrip_reveal"] = None

        # Page 1.5: Template Manager (created when needed)
        self.pages["template_manager"] = None

        # Start at login page
        self.setCurrentWidget(self.pages["login"])

    def connect_signals(self):
        """
        Connect page signals for navigation flow.

        Signal connections:
        - Login.authenticated → go_to_frame_selection()
        - FrameSelection.frame_selected → go_to_capture(frame_path)
        - FrameSelection.go_back → show_login()
        - Capture.retake_requested → go_to_frame_selection()
        - Capture.go_back → go_to_frame_selection() (with cleanup)
        - Capture.photostrip_ready → go_to_photostrip_reveal(pil_image)
        - PhotostripReveal.retake_requested → go_to_frame_selection()
        - PhotostripReveal.go_back → go_to_frame_selection()
        """
        # Login → Frame Selection
        self.pages["login"].authenticated.connect(self.go_to_frame_selection)

        # Frame Selection → Capture
        self.pages["frame_selection"].frame_selected.connect(self.go_to_capture)

        # Frame Selection → Login (back button)
        self.pages["frame_selection"].go_back.connect(self.show_login)

        # Frame Selection → Template Manager
        self.pages["frame_selection"].open_template_manager.connect(self.go_to_template_manager)

    def go_to_frame_selection(self):
        """
        Navigate to frame selection page.

        Called after successful authentication.
        """
        self.setCurrentWidget(self.pages["frame_selection"])

    def go_to_capture(self, frames_list: list):
        """
        Navigate to capture page with selected frames.

        Args:
            frames_list: List of tuples [(frame_path, frame_name), ...] for all 4 frame slots

        This method:
        1. Creates a new CaptureDisplayPage with the selected frames
        2. Cleans up the old capture page if it exists
        3. Connects signals for the new capture page
        4. Navigates to the capture page
        5. Initializes the camera
        """
        print(f"[DEBUG] go_to_capture called with frames_list={frames_list}")
        # Extract frame paths from tuples
        frame_paths = [f[0] for f in frames_list]
        # Create capture page with selected frames
        output_dir = "project_files/captured_images"
        config = LoginPage.load_config()
        photos_per_strip = config.get("photostrip", {}).get("photos_per_strip", 4)
        print(f"[DEBUG] Creating CaptureDisplayPage with photos_per_strip={photos_per_strip}, frame_paths={frame_paths}")
        capture_page = CaptureDisplayPage(frame_paths=frame_paths, output_dir=output_dir, photos_per_strip=photos_per_strip)

        print(f"[DEBUG] CaptureDisplayPage created successfully")

        # Clean up old capture page if exists
        if self.pages["capture"] is not None:
            print(f"[DEBUG] Cleaning up old capture page...")
            old_page = self.pages["capture"]
            old_page.cleanup()
            self.removeWidget(old_page)
            print(f"[DEBUG] Old capture page removed")

        # Add new capture page
        self.pages["capture"] = capture_page
        self.addWidget(capture_page)
        print(f"[DEBUG] Capture page added to stacked widget")

        # Connect signals
        capture_page.retake_requested.connect(self.go_to_frame_selection)
        capture_page.photostrip_ready.connect(self.go_to_photostrip_reveal)
        capture_page.go_back.connect(self._on_capture_go_back)
        print(f"[DEBUG] Signals connected")

        # Navigate and initialize camera
        print(f"[DEBUG] Setting current widget to capture page...")
        self.setCurrentWidget(capture_page)
        print(f"[DEBUG] Calling initialize_camera...")
        capture_page.initialize_camera()
        print(f"[DEBUG] go_to_capture complete")

    def go_to_photostrip_reveal(self, pil_image):
        """
        Navigate to photostrip reveal page with captured photo.

        Args:
            pil_image: PIL Image of the composed photostrip

        This method:
        1. Creates a new PhotostripRevealPage with the captured photo
        2. Cleans up the old reveal page if it exists
        3. Connects signals for the new reveal page
        4. Navigates to the reveal page
        """
        # Create photostrip reveal page with captured photo
        output_dir = "project_files/captured_images"
        reveal_page = PhotostripRevealPage(pil_image=pil_image, output_dir=output_dir)

        # Clean up old reveal page if exists
        if self.pages["photostrip_reveal"] is not None:
            old_page = self.pages["photostrip_reveal"]
            self.removeWidget(old_page)

        # Add new reveal page
        self.pages["photostrip_reveal"] = reveal_page
        self.addWidget(reveal_page)

        # Connect signals
        reveal_page.retake_requested.connect(self.go_to_frame_selection)
        reveal_page.go_back.connect(self.go_to_frame_selection)

        # Navigate to reveal page
        self.setCurrentWidget(reveal_page)

    def show_login(self):
        """
        Navigate back to login page.

        Called when back button is pressed on frame selection page.
        """
        self.setCurrentWidget(self.pages["login"])

    def _on_capture_go_back(self):
        """
        Handle go back from capture page.

        Cleans up capture page (releases camera) and returns to frame selection.
        """
        # Cleanup capture page
        if self.pages.get("capture"):
            self.pages["capture"].cleanup()

        # Return to frame selection
        self.setCurrentWidget(self.pages["frame_selection"])

    def go_to_template_manager(self):
        """Navigate to template manager page."""
        template_page = TemplateManagerPage()
        if self.pages["template_manager"] is not None:
            self.removeWidget(self.pages["template_manager"])
        self.pages["template_manager"] = template_page
        self.addWidget(template_page)
        template_page.template_selected.connect(self._on_template_selected)
        template_page.go_back.connect(self.go_to_frame_selection)
        self.setCurrentWidget(template_page)

    def _on_template_selected(self, frame_paths: list):
        """Handle template selection - apply to frame selection page."""
        from pathlib import Path
        frame_page = self.pages["frame_selection"]
        for i, frame_path in enumerate(frame_paths):
            if Path(frame_path).exists():
                frame_name = Path(frame_path).stem
                frame_page.selected_frames[i] = (frame_path, frame_name)
                frame_page.frame_slots[i].set_frame(frame_path, frame_name)
        frame_page._update_buttons()
        self.go_to_frame_selection()

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
        if self.pages.get("photostrip_reveal"):
            self.pages["photostrip_reveal"].cleanup()
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
