"""
FrameSlotCard Widget

A clickable card widget that displays one frame slot in a multi-photo photostrip.
Users can click to select a frame for each photo slot.

Features:
- Displays photo number ("PHOTO 1", "PHOTO 2", etc.)
- Shows frame thumbnail or placeholder for empty slot
- Emits clicked signal when clicked
- Visual feedback with green border when frame is assigned
"""

from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
import os
from pathlib import Path


class FrameSlotCard(QFrame):
    """
    A card widget representing a single photo slot in a multi-photo photostrip.

    The card displays:
    - Photo number label ("PHOTO 1", "PHOTO 2", etc.)
    - Thumbnail preview (160x160px) of selected frame or "+" placeholder

    Signals:
        clicked: Emitted when card is clicked. Emits slot_index (int)

    Attributes:
        slot_index: The index of this slot (0-3 for 4-photo strip)
        frame_path: Path to the selected frame image (None if empty)
        frame_name: Name of the selected frame (None if empty)
    """

    clicked = pyqtSignal(int)

    def __init__(self, slot_index: int, frame_path: str = None):
        """
        Initialize the FrameSlotCard.

        Args:
            slot_index: Index of this slot in the photostrip (0-based)
            frame_path: Optional path to a frame image to display
        """
        super().__init__()

        self.slot_index = slot_index
        self.frame_path = frame_path
        self.frame_name = None

        # Set fixed size for consistent card dimensions
        self.setFixedSize(180, 220)
        self.setCursor(Qt.PointingHandCursor)

        # Setup UI
        self._setup_ui()

        # Update thumbnail if frame path provided
        if self.frame_path:
            # Extract frame name from path
            self.frame_name = Path(self.frame_path).stem
            self.update_thumbnail()

        # Apply initial styling
        self._update_style()

    def _setup_ui(self):
        """Setup the UI components of the card."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Photo number label (e.g., "PHOTO 1", "PHOTO 2")
        self.photo_number_label = QLabel(f"PHOTO {self.slot_index + 1}")
        self.photo_number_label.setAlignment(Qt.AlignCenter)
        self.photo_number_label.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 14px;
                font-weight: bold;
                background-color: transparent;
            }
        """)

        # Thumbnail/placeholder label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(160, 160)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)

        # Show "+" placeholder for empty slot
        self.thumbnail_label.setText("+")
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 3px dashed #999999;
                border-radius: 8px;
                background-color: rgba(200, 200, 200, 0.3);
                color: #666666;
                font-size: 48px;
                font-weight: bold;
            }
        """)

        # Add widgets to layout
        layout.addWidget(self.photo_number_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.thumbnail_label, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def set_frame(self, frame_path: str, frame_name: str = None):
        """
        Set a frame for this slot and update the thumbnail.

        Args:
            frame_path: Path to the frame image file
            frame_name: Optional name for the frame (defaults to filename)
        """
        self.frame_path = frame_path

        if frame_name:
            self.frame_name = frame_name
        else:
            # Extract name from path if not provided
            self.frame_name = Path(frame_path).stem

        self.update_thumbnail()
        self._update_style()

    def clear_frame(self):
        """Clear the frame from this slot and reset to placeholder."""
        self.frame_path = None
        self.frame_name = None
        self.update_thumbnail()
        self._update_style()

    def update_thumbnail(self):
        """
        Update the thumbnail display based on current frame.

        If frame_path is set, loads and displays the frame image.
        Otherwise, shows the "+" placeholder.
        """
        if self.frame_path and os.path.exists(self.frame_path):
            # Load frame image
            pixmap = QPixmap(self.frame_path)

            if not pixmap.isNull():
                # Scale to fit thumbnail size
                scaled_pixmap = pixmap.scaled(
                    160, 160,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.thumbnail_label.setPixmap(scaled_pixmap)
            else:
                # Image failed to load - show error placeholder
                self.thumbnail_label.setText("⚠")
                self._set_error_thumbnail_style()
        else:
            # No frame set - show "+" placeholder
            self.thumbnail_label.setText("+")
            self._set_empty_thumbnail_style()

    def _set_empty_thumbnail_style(self):
        """Set thumbnail style for empty slot (dashed border, + placeholder)."""
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 3px dashed #999999;
                border-radius: 8px;
                background-color: rgba(200, 200, 200, 0.3);
                color: #666666;
                font-size: 48px;
                font-weight: bold;
            }
        """)

    def _set_filled_thumbnail_style(self):
        """Set thumbnail style for filled slot (green border, image)."""
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 3px solid #4CAF50;
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)

    def _set_error_thumbnail_style(self):
        """Set thumbnail style for error state (image failed to load)."""
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 3px solid #FFC0CB;
                border-radius: 8px;
                background-color: rgba(255, 192, 203, 0.3);
                color: #1A0A00;
                font-size: 48px;
                font-weight: bold;
            }
        """)

    def _update_style(self):
        """
        Update overall card styling based on selection state.

        Empty slot: Gray/dashed border with transparent background
        Has frame: Green border with slight gradient background
        """
        if self.frame_path:
            # Slot has a frame - green border style
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #FFE4C4,
                        stop:1 #FFDAB9
                    );
                    border: 3px solid #4CAF50;
                    border-radius: 12px;
                }
            """)
            self._set_filled_thumbnail_style()
        else:
            # Empty slot - gray dashed border
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.4);
                    border: 3px dashed #999999;
                    border-radius: 12px;
                }
            """)
            self._set_empty_thumbnail_style()

    def mousePressEvent(self, event):
        """
        Handle mouse click event.

        Emits the clicked signal with the slot index when clicked.
        """
        self.clicked.emit(self.slot_index)
        super().mousePressEvent(event)
