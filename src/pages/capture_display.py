from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QStackedWidget, QMessageBox)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import pyqtSignal
import os
from datetime import datetime
from pathlib import Path

from src.camera_handler import CameraHandler
from src.frame_composer import apply_frame


class CaptureDisplayPage(QWidget):
    """
    Capture and Display page for photobooth application.

    Two modes:
    1. Capture mode: Shows live camera feed with CAPTURE button
    2. Display mode: Shows captured photo with RETAKE/SAVE buttons
    """

    photo_saved = pyqtSignal(str)  # Signal emitted when photo is saved

    def __init__(self, frame_path: str, output_dir: str = "project_files/captured_images"):
        """Initialize the CaptureDisplayPage.

        Args:
            frame_path: Path to the frame overlay image
            output_dir: Directory where captured photos will be saved
        """
        super().__init__()

        self.frame_path = frame_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Camera and photo state
        self.camera_handler = None
        self.captured_photo = None
        self.composed_photo = None

        # Timer for camera feed
        self.feed_timer = QTimer()
        self.feed_timer.timeout.connect(self.update_camera_feed)

        # Setup UI
        self.setup_ui()

        # Initialize camera when widget is shown
        self.initialize_camera()

    def setup_ui(self):
        """Setup the user interface with stacked widget."""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Create stacked widget for capture/display modes
        self.stacked_widget = QStackedWidget()

        # Create capture widget
        self.capture_widget = self.create_capture_widget()
        self.stacked_widget.addWidget(self.capture_widget)

        # Create display widget
        self.display_widget = self.create_display_widget()
        self.stacked_widget.addWidget(self.display_widget)

        # Start in capture mode
        self.stacked_widget.setCurrentWidget(self.capture_widget)

        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # Apply FOFOBOOTH styling
        self.apply_fofoboth_style()

    def create_capture_widget(self) -> QWidget:
        """Create the capture mode widget with camera feed and CAPTURE button.

        Returns:
            QWidget configured for capture mode
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Title
        title = QLabel("CAPTURE YOUR PHOTO")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: bold;
                letter-spacing: 2px;
            }
        """)
        layout.addWidget(title)

        # Camera feed label
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: #222222;
                border: 3px solid #FFC0CB;
                border-radius: 12px;
            }
        """)
        self.camera_label.setText("Camera starting...")
        layout.addWidget(self.camera_label)

        # Capture button
        self.capture_button = QPushButton("CAPTURE")
        self.capture_button.setFixedHeight(60)
        self.capture_button.setCursor(Qt.PointingHandCursor)
        self.capture_button.clicked.connect(self.capture_photo)
        layout.addWidget(self.capture_button)

        widget.setLayout(layout)
        return widget

    def create_display_widget(self) -> QWidget:
        """Create the display mode widget with photo preview and action buttons.

        Returns:
            QWidget configured for display mode
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Title
        title = QLabel("YOUR PHOTO")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: bold;
                letter-spacing: 2px;
            }
        """)
        layout.addWidget(title)

        # Photo display label
        self.photo_label = QLabel()
        self.photo_label.setMinimumSize(640, 480)
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet("""
            QLabel {
                background-color: #222222;
                border: 3px solid #FFC0CB;
                border-radius: 12px;
            }
        """)
        layout.addWidget(self.photo_label)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        # Retake button
        self.retake_button = QPushButton("RETAKE")
        self.retake_button.setFixedHeight(60)
        self.retake_button.setCursor(Qt.PointingHandCursor)
        self.retake_button.clicked.connect(self.retake_photo)
        button_layout.addWidget(self.retake_button)

        # Save button
        self.save_button = QPushButton("SAVE")
        self.save_button.setFixedHeight(60)
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self.save_photo)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)
        widget.setLayout(layout)
        return widget

    def initialize_camera(self):
        """Initialize camera handler.

        Note: May fail if no camera hardware is available.
        """
        try:
            self.camera_handler = CameraHandler(device_index=0, width=1280, height=720)
            self.start_camera_feed()
        except RuntimeError as e:
            # Camera not available - show placeholder
            self.camera_label.setText(f"Camera not available\n{str(e)}")
            self.capture_button.setEnabled(False)

    def start_camera_feed(self):
        """Start the camera feed timer.

        Updates camera label at approximately 30 FPS.
        """
        if self.camera_handler:
            self.feed_timer.start(33)  # ~30 FPS

    def update_camera_feed(self):
        """Update camera label with latest frame from camera.

        Called periodically by feed_timer.
        """
        if self.camera_handler:
            try:
                pixmap = self.camera_handler.get_frame()
                scaled_pixmap = pixmap.scaled(
                    self.camera_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.camera_label.setPixmap(scaled_pixmap)
            except RuntimeError:
                self.camera_label.setText("Camera feed interrupted")

    def capture_photo(self):
        """Capture a photo from camera and apply frame overlay.

        Stops camera feed, captures photo, applies frame, and switches to display mode.
        """
        if not self.camera_handler:
            QMessageBox.warning(self, "Error", "Camera not available")
            return

        try:
            # Stop camera feed
            self.feed_timer.stop()

            # Capture photo from camera (BGR format)
            self.captured_photo = self.camera_handler.capture_photo()

            # Apply frame overlay
            self.composed_photo = apply_frame(self.captured_photo, self.frame_path)

            # Display result
            self.display_result()

            # Switch to display mode
            self.stacked_widget.setCurrentWidget(self.display_widget)

        except RuntimeError as e:
            QMessageBox.critical(self, "Error", f"Failed to capture photo: {str(e)}")
            self.retake_photo()

    def display_result(self):
        """Display the composed photo on the photo label.

        Converts PIL Image to QPixmap and scales to fit label.
        """
        if self.composed_photo:
            # Convert PIL Image to QPixmap
            from PIL.ImageQt import ImageQt
            qt_image = ImageQt(self.composed_photo)
            pixmap = QPixmap.fromImage(qt_image)

            # Scale to fit label
            scaled_pixmap = pixmap.scaled(
                self.photo_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.photo_label.setPixmap(scaled_pixmap)

    def retake_photo(self):
        """Return to capture mode for retaking photo.

        Clears current photo and restarts camera feed.
        """
        # Clear current photo
        self.captured_photo = None
        self.composed_photo = None
        self.photo_label.clear()

        # Switch to capture mode
        self.stacked_widget.setCurrentWidget(self.capture_widget)

        # Restart camera feed
        self.start_camera_feed()

    def save_photo(self):
        """Save the composed photo to disk with timestamp.

        Photo is saved to output_dir with filename: photo_YYYYMMDD_HHMMSS.png
        Emits photo_saved signal with file path.
        """
        if not self.composed_photo:
            QMessageBox.warning(self, "Error", "No photo to save")
            return

        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.png"
            filepath = self.output_dir / filename

            # Save photo
            self.composed_photo.save(str(filepath))

            # Show success message
            QMessageBox.information(
                self,
                "Photo Saved",
                f"Photo saved successfully!\n\n{filepath}"
            )

            # Emit signal
            self.photo_saved.emit(str(filepath))

            # Return to capture mode after saving
            self.retake_photo()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save photo: {str(e)}")

    def cleanup(self):
        """Release camera resources.

        Should be called when page is closed or navigation occurs.
        """
        # Stop camera feed timer
        self.feed_timer.stop()

        # Release camera
        if self.camera_handler:
            self.camera_handler.release()
            self.camera_handler = None

    def apply_fofoboth_style(self):
        """Apply FOFOBOOTH-inspired styling to buttons."""
        button_style = """
            QPushButton {
                background-color: #FFC0CB;
                color: #333333;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #FFB6C1;
            }
            QPushButton:pressed {
                background-color: #FFA0B0;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """

        self.capture_button.setStyleSheet(button_style)
        self.retake_button.setStyleSheet(button_style)
        self.save_button.setStyleSheet(button_style)

    def showEvent(self, event):
        """Handle show event - initialize camera when page is shown."""
        super().showEvent(event)
        if not self.camera_handler:
            self.initialize_camera()

    def hideEvent(self, event):
        """Handle hide event - cleanup camera when page is hidden."""
        super().hideEvent(event)
        self.cleanup()
