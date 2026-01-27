from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QMessageBox, QFileDialog)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Platform-specific printing
if sys.platform == "win32":
    import win32print


class PhotostripRevealPage(QWidget):
    """
    Photostrip Reveal page for displaying the final composed photo.

    This page shows the captured photo with frame overlay and provides
    options to download, retake, or print the photostrip.
    """

    download_requested = pyqtSignal()  # Signal emitted when download is requested
    retake_requested = pyqtSignal()  # Signal emitted when retake is requested
    go_back = pyqtSignal()  # Signal emitted when back button is clicked

    def __init__(self, pil_image=None, output_dir: str = "project_files/captured_images"):
        """Initialize the PhotostripRevealPage.

        Args:
            pil_image: PIL Image object to display
            output_dir: Directory where photostrips will be saved
        """
        super().__init__()

        self.pil_image = pil_image
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Setup UI
        self.setup_ui()

        # Display the photostrip if provided
        if pil_image:
            self.display_photostrip(pil_image)

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Back button
        self.back_button = QPushButton("← BACK")
        self.back_button.setFixedSize(100, 40)
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self._on_back_clicked)
        self.back_button.setParent(self)
        self.back_button.move(20, 20)
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

        # Title
        title = QLabel("YOUR PHOTOSTRIP!")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 2px;
            }
        """)
        layout.addWidget(title)

        # Photostrip display label
        self.photostrip_label = QLabel()
        self.photostrip_label.setMinimumSize(640, 480)
        self.photostrip_label.setAlignment(Qt.AlignCenter)
        self.photostrip_label.setStyleSheet("""
            QLabel {
                background-color: #222222;
                border: 3px solid #FFC0CB;
                border-radius: 12px;
            }
        """)
        self.photostrip_label.setText("Loading photostrip...")
        layout.addWidget(self.photostrip_label)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        # Download button
        self.download_button = QPushButton("⬇ DOWNLOAD")
        self.download_button.setFixedHeight(60)
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.clicked.connect(self.download_photostrip)
        button_layout.addWidget(self.download_button)

        # Print button
        self.print_button = QPushButton("🖨 PRINT")
        self.print_button.setFixedHeight(60)
        self.print_button.setCursor(Qt.PointingHandCursor)
        self.print_button.clicked.connect(self.print_photostrip)
        button_layout.addWidget(self.print_button)

        # Retake button
        self.retake_button = QPushButton("↺ RETAKE")
        self.retake_button.setFixedHeight(60)
        self.retake_button.setCursor(Qt.PointingHandCursor)
        self.retake_button.clicked.connect(self._on_retake_clicked)
        button_layout.addWidget(self.retake_button)

        layout.addLayout(button_layout)
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

    def display_photostrip(self, pil_image):
        """Display the photostrip image.

        Args:
            pil_image: PIL Image object to display
        """
        self.pil_image = pil_image

        # Convert PIL Image to QPixmap
        from PyQt5.QtGui import QImage

        # Ensure image is in RGB mode
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Get image data as bytes
        width, height = pil_image.size
        img_bytes = pil_image.tobytes()

        # Create QImage from bytes (Format_RGB888 for 24-bit RGB)
        qt_image = QImage(img_bytes, width, height, width * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)

        # Scale to fit label with aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.photostrip_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.photostrip_label.setPixmap(scaled_pixmap)

    def download_photostrip(self):
        """Download/save the photostrip to disk."""
        if not self.pil_image:
            QMessageBox.warning(self, "Error", "No photostrip to download")
            return

        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photostrip_{timestamp}.png"
            filepath = self.output_dir / filename

            # Save photo
            self.pil_image.save(str(filepath))

            # Show success message
            QMessageBox.information(
                self,
                "Photostrip Saved",
                f"Photostrip saved successfully!\n\n{filepath}"
            )

            # Emit signal
            self.download_requested.emit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save photostrip: {str(e)}")

    def print_photostrip(self):
        """Print the photostrip to the default printer."""
        if not self.pil_image:
            QMessageBox.warning(self, "Error", "No photostrip to print")
            return

        try:
            # Create a temporary file for printing
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                # Save the image to temp file
                self.pil_image.save(tmp_path)

            if sys.platform == "win32":
                # Windows: Use win32print to print
                try:
                    # Open the default printer
                    printer_name = win32print.GetDefaultPrinter()

                    # Open the printer device
                    hPrinter = win32print.OpenPrinter(printer_name)

                    # Start print job
                    win32print.StartDocPrinter(hPrinter, f"Photostrip_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

                    # Read the image file and send to printer
                    with open(tmp_path, "rb") as f:
                        data = f.read()
                        win32print.WritePrinter(hPrinter, data)

                    # End print job
                    win32print.EndDocPrinter(hPrinter)

                    # Close printer
                    win32print.ClosePrinter(hPrinter)

                    # Clean up temp file
                    os.unlink(tmp_path)

                    QMessageBox.information(
                        self,
                        "Print Successful",
                        "Photostrip has been sent to the printer!"
                    )

                except Exception as e:
                    # Clean up temp file if print failed
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    raise

            else:
                # Other platforms: Use system print dialog
                import subprocess
                try:
                    if sys.platform == "darwin":
                        # macOS: Use lpr
                        subprocess.run(["lpr", tmp_path], check=True)
                    else:
                        # Linux: Use xdg-open or lpr
                        try:
                            subprocess.run(["xdg-open", tmp_path], check=True)
                        except:
                            subprocess.run(["lpr", tmp_path], check=True)

                    QMessageBox.information(
                        self,
                        "Print Successful",
                        "Photostrip has been sent to the printer!"
                    )
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Print Error",
                f"Failed to print photostrip:\n\n{str(e)}\n\nMake sure you have a printer connected and configured."
            )

    def _on_retake_clicked(self):
        """Handle retake button click - emit signal."""
        self.retake_requested.emit()

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

        self.download_button.setStyleSheet(button_style)
        self.print_button.setStyleSheet(button_style)
        self.retake_button.setStyleSheet(button_style)

    def showEvent(self, event):
        """Handle show event - refresh display when page is shown."""
        super().showEvent(event)
        if self.pil_image:
            self.display_photostrip(self.pil_image)

        # Position back button in top-left corner and raise to top
        if hasattr(self, 'back_button'):
            self.back_button.move(20, 20)
            self.back_button.raise_()

    def _on_back_clicked(self):
        """Handle back button click - emit go_back signal."""
        self.go_back.emit()

    def cleanup(self):
        """Cleanup resources when page is closed."""
        # No specific cleanup needed for this page
        pass

    def closeEvent(self, event):
        """Handle close event - ensure cleanup is called."""
        self.cleanup()
        super().closeEvent(event)
