from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QStackedWidget, QMessageBox, QSlider)
from PyQt5.QtGui import QPixmap, QFont, QPalette, QImage
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtCore import pyqtSignal
import os
import cv2
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

    photo_saved = pyqtSignal(str)  # Signal emitted when photo is saved (deprecated)
    retake_requested = pyqtSignal()  # Signal emitted when retake is requested
    photostrip_ready = pyqtSignal(object)  # Signal emitted with PIL Image when ready for Page 3
    go_back = pyqtSignal()  # Signal emitted when back button is clicked

    def __init__(self, frame_paths: list, output_dir: str = "project_files/captured_images", photos_per_strip: int = 4):
        """Initialize the CaptureDisplayPage.

        Args:
            frame_paths: List of paths to frame overlay images (one per photo)
            output_dir: Directory where captured photos will be saved
            photos_per_strip: Number of photos to capture for the strip (default: 4)
        """
        super().__init__()

        print(f"[DEBUG] CaptureDisplayPage.__init__ called with frame_paths={frame_paths}, photos_per_strip={photos_per_strip}")

        # Validate frame_paths
        if len(frame_paths) not in (4, 9):
            raise ValueError(f"Expected 4 or 9 frame paths (one per photo), got {len(frame_paths)}")
        self.frame_paths = frame_paths
        for frame_path in frame_paths:
            if not Path(frame_path).exists():
                raise ValueError(f"Frame file not found: {frame_path}")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Camera and photo state
        self.camera_handler = None
        self.captured_photos = []  # List to store captured photos
        self.current_photo_index = 0  # Which photo we're on (0-based)
        self.current_capture = None  # Temporary holding for preview
        self.photos_per_strip = photos_per_strip  # Total photos needed
        self.final_image = None  # Composed photostrip
        self.current_exposure = 0.0  # Current exposure value for this photo
        self.exposure_values = []  # List to store exposure value for each captured photo

        print(f"[DEBUG] Variables initialized, calling setup_ui...")

        # Countdown state
        self.countdown_value = 3
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)

        # Timer for camera feed
        self.feed_timer = QTimer()
        self.feed_timer.timeout.connect(self.update_camera_feed)

        # Setup UI
        self.setup_ui()

        print(f"[DEBUG] setup_ui complete, calling initialize_camera...")

        # Initialize camera when widget is shown
        self.initialize_camera()

        print(f"[DEBUG] CaptureDisplayPage.__init__ complete")

    def setup_ui(self):
        """Setup the user interface with stacked widget."""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Create stacked widget for capture/preview modes
        self.stacked_widget = QStackedWidget()

        # Create capture widget
        self.capture_widget = self.create_capture_widget()
        self.stacked_widget.addWidget(self.capture_widget)

        # Create preview widget (for single photo review)
        self.preview_widget = self.create_preview_widget()
        self.stacked_widget.addWidget(self.preview_widget)

        # Start in capture mode
        self.stacked_widget.setCurrentWidget(self.capture_widget)

        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # Apply FOFOBOOTH styling with seashell gradient
        self.apply_stylesheet()

        # Apply seashell background to page
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFF8DC,
                    stop:0.3 #FFF0E0,
                    stop:0.6 #FFE4C4,
                    stop:1 #FFDAB9
                );
            }
        """)

    def create_capture_widget(self) -> QWidget:
        """Create the capture mode widget with camera feed and CAPTURE button.

        Returns:
            QWidget configured for capture mode
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Back button (will be positioned via parent in showEvent)
        self.back_button = QPushButton("← BACK")
        self.back_button.setFixedSize(100, 40)
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self._on_back_clicked)
        self.back_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFE4C4,
                    stop:1 #FFDAB9
                );
                color: #1A0A00;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #1A0A00;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFDAB9,
                    stop:1 #FFCBA4
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFCBA4,
                    stop:1 #E8B090
                );
            }
        """)
        self.back_button.setParent(widget)
        self.back_button.raise_()  # Ensure button is on top

        # Title
        title = QLabel("PHOTO TIME!")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 28px;
                font-weight: bold;
                letter-spacing: 2px;
                background-color: transparent;
            }
        """)
        layout.addWidget(title)

        # Progress indicator
        self.progress_label = QLabel("Photo 1 of 4")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 18px;
                font-weight: bold;
                background-color: transparent;
                padding: 10px;
            }
        """)
        layout.addWidget(self.progress_label)
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

        # Exposure adjustment slider
        exposure_layout = QHBoxLayout()
        exposure_layout.setSpacing(15)

        exposure_label = QLabel("Exposure:")
        exposure_label.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
                padding: 5px;
            }
        """)
        exposure_layout.addWidget(exposure_label)

        self.exposure_slider = QSlider(Qt.Horizontal)
        self.exposure_slider.setRange(-20, 20)  # -2.0 to +2.0 (divide by 10)
        self.exposure_slider.setValue(0)  # Default: no adjustment
        self.exposure_slider.setFixedWidth(300)
        self.exposure_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 2px solid #1A0A00;
                height: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #888888, stop:0.5 #FFFFFF, stop:1 #CCCCCC);
                border-radius: 6px;
            }
            QSlider::handle:horizontal {
                background: #FFC0CB;
                border: 2px solid #1A0A00;
                width: 24px;
                height: 24px;
                margin: -6px 0;
                border-radius: 12px;
            }
            QSlider::handle:horizontal:hover {
                background: #FFDAB9;
            }
        """)
        self.exposure_slider.valueChanged.connect(self._on_exposure_changed)
        exposure_layout.addWidget(self.exposure_slider)

        self.exposure_value_label = QLabel("0.0")
        self.exposure_value_label.setFixedWidth(40)
        self.exposure_value_label.setAlignment(Qt.AlignCenter)
        self.exposure_value_label.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
                padding: 5px;
            }
        """)
        exposure_layout.addWidget(self.exposure_value_label)

        exposure_container = QWidget()
        exposure_container.setLayout(exposure_layout)
        exposure_container.setMaximumWidth(500)
        layout.addWidget(exposure_container, alignment=Qt.AlignCenter)

        # Countdown overlay label (hidden initially)
        self.countdown_label = QLabel(self.camera_label)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setVisible(False)
        self.countdown_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 150);
                color: #FFC0CB;
                font-size: 120px;
                font-weight: bold;
                border-radius: 20px;
                padding: 40px;
            }
        """)

        # Frame overlay label (shows frame image on top of camera feed)
        self.frame_overlay_label = QLabel(self.camera_label)
        self.frame_overlay_label.setAlignment(Qt.AlignCenter)
        self.frame_overlay_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        # Enable transparency for the label itself
        self.frame_overlay_label.setAttribute(Qt.WA_TranslucentBackground)

        # Load frame images for overlay (one per photo)
        from PyQt5.QtGui import QPixmap
        self.frame_pixmaps_original = []
        for frame_path in self.frame_paths:
            pixmap = QPixmap(frame_path)
            self.frame_pixmaps_original.append(pixmap)
        self.frame_pixmap_scaled = None  # Will hold the scaled/cropped version
        # Show overlay if at least one frame loaded successfully
        if any(not pixmap.isNull() for pixmap in self.frame_pixmaps_original):
            self.frame_overlay_label.show()
        else:
            self.frame_overlay_label.hide()

        # Ensure countdown label is above frame overlay
        self.countdown_label.raise_()

        # Capture button
        self.capture_button = QPushButton("📷 CAPTURE")
        self.capture_button.setFixedHeight(60)
        self.capture_button.setCursor(Qt.PointingHandCursor)
        self.capture_button.clicked.connect(self.start_countdown)
        layout.addWidget(self.capture_button)

        widget.setLayout(layout)
        return widget

    def _on_exposure_changed(self, value: int):
        """Handle exposure slider value change.

        Args:
            value: Slider value (-20 to +20, divide by 10 for actual exposure)
        """
        exposure = value / 10.0  # Convert to -2.0 to +2.0 range
        self.current_exposure = exposure
        self.exposure_value_label.setText(f"{exposure:+.1f}")

    def create_preview_widget(self) -> QWidget:
        """Create the preview widget for single photo review.

        Shows the captured photo with KEEP & NEXT and RETAKE buttons.

        Returns:
            QWidget configured for preview mode
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Title
        title = QLabel("REVIEW YOUR PHOTO")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 28px;
                font-weight: bold;
                letter-spacing: 2px;
                background-color: transparent;
            }
        """)
        layout.addWidget(title)

        # Photo display label
        self.preview_photo_label = QLabel()
        self.preview_photo_label.setMinimumSize(640, 480)
        self.preview_photo_label.setAlignment(Qt.AlignCenter)
        self.preview_photo_label.setStyleSheet("""
            QLabel {
                background-color: #222222;
                border: 3px solid #D4A574;
                border-radius: 12px;
            }
        """)
        layout.addWidget(self.preview_photo_label)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        # Retake button
        self.preview_retake_button = QPushButton("↺ RETAKE THIS PHOTO")
        self.preview_retake_button.setFixedHeight(60)
        self.preview_retake_button.setCursor(Qt.PointingHandCursor)
        self.preview_retake_button.clicked.connect(self.retake_current_photo)
        button_layout.addWidget(self.preview_retake_button)

        # Keep & Next button
        self.keep_next_button = QPushButton("✓ KEEP & NEXT")
        self.keep_next_button.setFixedHeight(60)
        self.keep_next_button.setCursor(Qt.PointingHandCursor)
        self.keep_next_button.clicked.connect(self.accept_and_next_photo)
        button_layout.addWidget(self.keep_next_button)

        layout.addLayout(button_layout)
        widget.setLayout(layout)
        return widget

    def initialize_camera(self):
        """Initialize camera handler.

        Note: May fail if no camera hardware is available.
        """
        print(f"[DEBUG] initialize_camera called")
        try:
            print(f"[DEBUG] Creating CameraHandler...")
            self.camera_handler = CameraHandler(device_index=0, width=1280, height=720)
            print(f"[DEBUG] CameraHandler created successfully")
            print(f"[DEBUG] Starting camera feed...")
            self.start_camera_feed()
            print(f"[DEBUG] Camera feed started")
        except RuntimeError as e:
            # Camera not available - show placeholder
            print(f"[DEBUG] Camera error: {e}")
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

        Called periodically by feed_timer. Applies exposure adjustment if set.
        """
        if self.camera_handler:
            try:
                # Get raw frame from camera
                from src.exposure_utils import apply_exposure

                # Capture raw frame (we need access to the underlying frame data)
                ret, frame = self.camera_handler.camera.read()
                if not ret:
                    raise RuntimeError("Failed to read frame from camera")

                # Apply exposure adjustment if set
                if self.current_exposure != 0.0:
                    frame = apply_exposure(frame, self.current_exposure)

                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to QImage
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

                # Convert to QPixmap
                pixmap = QPixmap.fromImage(qt_image)
                scaled_pixmap = pixmap.scaled(
                    self.camera_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.camera_label.setPixmap(scaled_pixmap)

                # Reposition frame overlay when camera feed updates
                self._position_frame_overlay()
            except RuntimeError:
                self.camera_label.setText("Camera feed interrupted")

    def start_countdown(self):
        """Start countdown timer before photo capture."""
        if not self.camera_handler:
            QMessageBox.warning(self, "Error", "Camera not available")
            return

        # Disable capture button during countdown
        self.capture_button.setEnabled(False)

        # Initialize countdown
        self.countdown_value = 3
        self.show_countdown()

        # Start countdown timer (1 second intervals)
        self.countdown_timer.start(1000)

    def show_countdown(self):
        """Display countdown overlay on camera feed."""
        self.countdown_label.setText(str(self.countdown_value))
        self.countdown_label.setVisible(True)

        # Center the countdown label over the camera feed
        label_size = self.camera_label.size()
        overlay_size = self.countdown_label.sizeHint()
        x = (label_size.width() - overlay_size.width()) // 2
        y = (label_size.height() - overlay_size.height()) // 2
        self.countdown_label.move(x, y)
        self.countdown_label.resize(overlay_size)

        # Raise countdown label to be above frame overlay
        self.countdown_label.raise_()

    def _position_frame_overlay(self):
        """Position the frame overlay over the camera feed, cropping frame to fit exactly."""
        # Use the frame for the current photo index
        frame_pixmap_original = self.frame_pixmaps_original[self.current_photo_index] if self.current_photo_index < len(self.frame_pixmaps_original) else self.frame_pixmaps_original[0]

        if not frame_pixmap_original.isNull():
            label_size = self.camera_label.size()
            frame_size = frame_pixmap_original.size()

            # Calculate scaling to make frame cover the camera area (crop frame if needed)
            scale_x = label_size.width() / frame_size.width()
            scale_y = label_size.height() / frame_size.height()
            scale = max(scale_x, scale_y)  # Use larger scale to cover entire area

            # Scale frame to cover camera area
            scaled_width = int(frame_size.width() * scale)
            scaled_height = int(frame_size.height() * scale)
            frame_scaled = frame_pixmap_original.scaled(
                scaled_width, scaled_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # Crop the scaled frame to match camera label size exactly (centered)
            crop_x = (scaled_width - label_size.width()) // 2
            crop_y = (scaled_height - label_size.height()) // 2

            # Create a cropped pixmap
            from PyQt5.QtGui import QPixmap
            self.frame_pixmap_scaled = frame_scaled.copy(crop_x, crop_y, label_size.width(), label_size.height())

            self.frame_overlay_label.setPixmap(self.frame_pixmap_scaled)
            self.frame_overlay_label.setGeometry(0, 0, label_size.width(), label_size.height())

    def update_countdown(self):
        """Update countdown value and capture photo when countdown reaches zero."""
        self.countdown_value -= 1

        if self.countdown_value > 0:
            # Show next countdown number
            self.show_countdown()
        else:
            # Countdown finished - capture photo
            self.countdown_timer.stop()
            self.countdown_label.setVisible(False)
            self.capture_photo()

    def capture_photo(self):
        """Capture a photo from camera and show preview.

        Stops camera feed, captures photo, shows preview with KEEP/NEXT/RETAKE options.
        """
        if not self.camera_handler:
            QMessageBox.warning(self, "Error", "Camera not available")
            return

        try:
            # Stop camera feed
            self.feed_timer.stop()

            # Get the displayed size from camera_label to match preview
            displayed_size = self.camera_label.size()
            print(f"[DEBUG] Capturing photo at displayed size: {displayed_size.width()}x{displayed_size.height()}")

            # Capture photo from camera at the displayed dimensions to match preview
            self.current_capture = self.camera_handler.capture_photo(
                target_width=displayed_size.width(),
                target_height=displayed_size.height()
            )

            # Store the exposure value used for this capture
            self.exposure_values.append(self.current_exposure)

            # Apply frame overlay (use frame for current photo index)
            frame_index = self.current_photo_index if self.current_photo_index < len(self.frame_paths) else 0
            print(f"[DEBUG] Applying frame at index {frame_index} (current_photo_index={self.current_photo_index})")
            framed_photo = apply_frame(self.current_capture, self.frame_paths[frame_index])

            # Display preview
            self.display_photo_preview(framed_photo)

            # Switch to preview mode
            self.stacked_widget.setCurrentWidget(self.preview_widget)

            # Re-enable capture button (for next photo)
            self.capture_button.setEnabled(True)

        except RuntimeError as e:
            QMessageBox.critical(self, "Error", f"Failed to capture photo: {str(e)}")
            self.retake_current_photo()
            self.capture_button.setEnabled(True)

    def save_photo(self):
        """Emit photostrip_ready signal to navigate to Page 3.

        The photo is NOT saved to disk yet - only the DOWNLOAD button on Page 3 saves the file.
        Emits photostrip_ready signal with PIL Image for Page 3 display.
        """
        if not self.final_image:
            QMessageBox.warning(self, "Error", "No photo to save")
            return

        # Emit signal with PIL Image for Page 3 (no file save here)
        self.photostrip_ready.emit(self.final_image)

    def display_photo_preview(self, framed_photo):
        """Display the captured photo in preview mode.

        Args:
            framed_photo: PIL Image of the captured photo with frame applied
        """
        # Ensure image is in RGB mode
        if framed_photo.mode != 'RGB':
            framed_photo = framed_photo.convert('RGB')

        # Get image data as bytes
        width, height = framed_photo.size
        img_bytes = framed_photo.tobytes()

        # Create QImage from bytes
        qt_image = QImage(img_bytes, width, height, width * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)

        # Scale to fit label
        scaled_pixmap = pixmap.scaled(
            self.preview_photo_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.preview_photo_label.setPixmap(scaled_pixmap)

    def accept_and_next_photo(self):
        """Accept the current photo and move to the next one.

        Adds current photo to captured_photos list and increments index.
        If all photos captured, composes strip and navigates to Page 3.
        """
        # Add the original captured photo (without frame) to list
        if self.current_capture is not None:
            self.captured_photos.append(self.current_capture)
            print(f"[DEBUG] Photo accepted. captured_photos count: {len(self.captured_photos)}, current_photo_index: {self.current_photo_index}")

        # Increment to next photo
        self.current_photo_index += 1
        print(f"[DEBUG] Incremented current_photo_index to: {self.current_photo_index}, photos_per_strip: {self.photos_per_strip}")

        if self.current_photo_index >= self.photos_per_strip:
            # All photos captured - compose and proceed
            print(f"[DEBUG] All photos captured. Calling compose_and_proceed with {len(self.captured_photos)} photos")
            self.compose_and_proceed()
        else:
            # More photos needed - return to capture mode
            print(f"[DEBUG] More photos needed. Returning to capture mode.")
            self.return_to_capture_mode()

    def retake_current_photo(self):
        """Retake the current photo.

        Discards the current capture, resets exposure, and returns to capture mode.
        """
        # Clear current capture
        self.current_capture = None

        # Reset exposure slider for the retake
        self.exposure_slider.setValue(0)
        self.current_exposure = 0.0

        # Return to capture mode
        self.return_to_capture_mode()

    def return_to_capture_mode(self):
        """Return to capture mode for next photo.

        Updates progress label, resets exposure slider, and restarts camera feed.
        """
        # Update progress label
        photo_num = self.current_photo_index + 1
        self.progress_label.setText(f"Photo {photo_num} of {self.photos_per_strip}")

        # Reset exposure slider to default for next photo
        self.exposure_slider.setValue(0)
        self.current_exposure = 0.0

        # Clear preview
        self.preview_photo_label.clear()

        # Switch back to capture mode
        self.stacked_widget.setCurrentWidget(self.capture_widget)

        # Restart camera feed
        self.start_camera_feed()

    def compose_and_proceed(self):
        """Compose all captured photos into a photostrip and proceed to Page 3.

        Creates vertical strip from all captured photos with frame applied.
        """
        print(f"[DEBUG] compose_and_proceed: captured_photos={len(self.captured_photos)}, photos_per_strip={self.photos_per_strip}")
        print(f"[DEBUG] compose_and_proceed: frame_paths={len(self.frame_paths)}")

        if len(self.captured_photos) != self.photos_per_strip:
            QMessageBox.warning(self, "Error", f"Expected {self.photos_per_strip} photos, got {len(self.captured_photos)}")
            return

        try:
            # Import composer function
            from src.frame_composer import compose_photostrip

            print(f"[DEBUG] compose_and_proceed: Calling compose_photostrip...")

            # Compose vertical strip with all frame paths and exposure values
            self.final_image = compose_photostrip(
                self.captured_photos,
                self.frame_paths,
                exposure_values=self.exposure_values
            )

            print(f"[DEBUG] compose_and_proceed: Photostrip composed successfully")

            # Navigate to Page 3
            self.photostrip_ready.emit(self.final_image)

        except Exception as e:
            print(f"[DEBUG] compose_and_proceed ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to compose photostrip: {str(e)}")
            # Return to capture mode as fallback
            self.return_to_capture_mode()

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

    def closeEvent(self, event):
        """Handle close event - ensure camera is released."""
        self.cleanup()
        super().closeEvent(event)

    def apply_stylesheet(self):
        """Apply seashell gradient styling to buttons."""
        button_style = """
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFE4C4,
                    stop:1 #FFDAB9
                );
                color: #1A0A00;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid #1A0A00;
                border-radius: 10px;
                padding: 15px 30px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFDAB9,
                    stop:1 #FFCBA4
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFCBA4,
                    stop:1 #E8B090
                );
            }
            QPushButton:disabled {
                background-color: rgba(200, 180, 160, 0.5);
                color: rgba(26, 10, 0, 0.5);
                border: 2px solid rgba(26, 10, 0, 0.3);
            }
        """

        self.capture_button.setStyleSheet(button_style)
        if hasattr(self, 'preview_retake_button'):
            self.preview_retake_button.setStyleSheet(button_style)
        if hasattr(self, 'keep_next_button'):
            self.keep_next_button.setStyleSheet(button_style)

    def showEvent(self, event):
        """Handle show event - initialize camera when page is shown."""
        super().showEvent(event)
        if not self.camera_handler:
            self.initialize_camera()

        # Position back button in top-left corner and raise to top
        if hasattr(self, 'back_button'):
            self.back_button.move(20, 20)
            self.back_button.raise_()

        # Update progress label
        photo_num = self.current_photo_index + 1
        self.progress_label.setText(f"Photo {photo_num} of {self.photos_per_strip}")

        # Position frame overlay when page is shown
        self._position_frame_overlay()

    def _on_back_clicked(self):
        """Handle back button click - show confirmation if photos are captured."""
        photo_count = len(self.captured_photos)
        if self.current_capture is not None:
            photo_count += 1

        if photo_count > 0 or self.final_image:
            # User has captured photos - confirm before going back
            reply = QMessageBox.question(
                self,
                "Go Back?",
                f"You have {photo_count} captured photo(s). Going back will lose these photos.\n\nDo you want to go back?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Cleanup and emit go_back signal
                self.captured_photos.clear()
                self.exposure_values.clear()
                self.current_photo_index = 0
                self.cleanup()
                self.go_back.emit()
        else:
            # No photos captured - just go back
            self.go_back.emit()

    def hideEvent(self, event):
        """Handle hide event - cleanup camera when page is hidden."""
        super().hideEvent(event)
        self.cleanup()
