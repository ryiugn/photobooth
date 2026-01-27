"""
FramePickerDialog Widget

A modal dialog that displays available frames for selection.
Users can browse and select a frame for a photo slot in the photostrip.

Features:
- Modal dialog with fixed size (800x600)
- Displays available frames in a scrollable grid (3 columns)
- Click frame card to select and close dialog
- Cancel button to close without selection
- Seashell gradient background matching app theme
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QGridLayout, QFrame, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
import os
from pathlib import Path


class FramePickerDialog(QDialog):
    """
    A modal dialog for selecting a frame from the available frames.

    The dialog displays all available frame images in a scrollable grid.
    Users can click on a frame to select it, which closes the dialog and
    returns the selected frame path and name.

    Usage:
        dialog = FramePickerDialog(frames_dir="project_files/frames")
        if dialog.exec_() == QDialog.Accepted:
            frame_path, frame_name = dialog.get_selected_frame()
            # Use selected frame...

    Attributes:
        frames_dir: Directory containing frame images
        frames: List of (frame_path, frame_name) tuples
        selected_frame: Path to the selected frame (None if cancelled)
        selected_name: Name of the selected frame (None if cancelled)
    """

    def __init__(self, frames_dir="project_files/frames", parent=None):
        """
        Initialize the FramePickerDialog.

        Args:
            frames_dir: Path to directory containing frame images
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.frames_dir = frames_dir
        self.frames = []  # List of (path, name) tuples
        self.selected_frame = None  # Path to selected frame
        self.selected_name = None  # Name of selected frame

        # Configure dialog properties
        self.setModal(True)
        self.setFixedSize(800, 600)
        self.setWindowTitle("Select a Frame")

        # Load frames and setup UI
        self._load_frames()
        self._setup_ui()

    def _load_frames(self):
        """
        Load frame images from the frames directory.

        Supports .png, .jpg, .jpeg, and .webp formats.
        Frames are sorted alphabetically by filename.
        Skips files that don't exist gracefully.
        """
        frames_path = Path(self.frames_dir)

        # Create directory if it doesn't exist
        if not frames_path.exists():
            frames_path.mkdir(parents=True, exist_ok=True)

        # Support .png, .jpg, .jpeg, .webp (case-insensitive)
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.PNG', '*.JPG', '*.JPEG', '*.WEBP']:
            for frame_file in frames_path.glob(ext):
                # Skip if file doesn't exist (handles broken symlinks, etc.)
                if not frame_file.is_file():
                    continue

                self.frames.append((str(frame_file), frame_file.stem))

        # Sort alphabetically by name
        self.frames.sort(key=lambda x: x[1])

    def _setup_ui(self):
        """Set up the user interface for the dialog."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title label
        title = QLabel("CHOOSE A FRAME")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 32px;
                font-weight: bold;
                background-color: transparent;
                padding: 15px;
                text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8);
            }
        """)
        layout.addWidget(title)

        # Scroll area for frame grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #444444;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #FFC0CB;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Container widget for grid
        scroll_widget = QWidget()
        scroll_widget.setObjectName("scroll_widget")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        # Grid layout for frame cards (3 columns)
        grid = QGridLayout()
        grid.setSpacing(20)
        grid.setContentsMargins(20, 20, 20, 20)

        # Create frame cards
        cols = 3  # Number of columns in grid
        for idx, (frame_path, frame_name) in enumerate(self.frames):
            card = self._create_frame_card(frame_path, frame_name, idx)

            row = idx // cols
            col = idx % cols
            grid.addWidget(card, row, col)

        # Add spacer to center grid if fewer items
        if len(self.frames) > 0:
            last_row = (len(self.frames) - 1) // cols
            grid.setRowStretch(last_row + 1, 1)

        scroll_layout.addLayout(grid)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area, stretch=1)

        # Cancel button
        self.cancel_button = QPushButton("CANCEL")
        self.cancel_button.setFixedSize(200, 50)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFE4C4,
                    stop:1 #FFDAB9
                );
                color: #1A0A00;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #1A0A00;
                border-radius: 10px;
                padding: 12px 24px;
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

        # Center cancel button
        button_container = QHBoxLayout()
        button_container.addStretch()
        button_container.addWidget(self.cancel_button)
        button_container.addStretch()
        layout.addLayout(button_container)

        self.setLayout(layout)

        # Apply seashell gradient background (#FFF8DC to #FFDAB9)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFF8DC,
                    stop:0.3 #FFF0E0,
                    stop:0.6 #FFE4C4,
                    stop:1 #FFDAB9
                );
            }
        """)

    def _create_frame_card(self, frame_path, frame_name, index):
        """
        Create a clickable frame card widget.

        The card displays:
        - Frame thumbnail (180x180px)
        - Frame name (formatted title case)
        - Hover effect for better UX

        Args:
            frame_path: Path to the frame image file
            frame_name: Name of the frame (filename without extension)
            index: Index of the frame in the list

        Returns:
            QFrame: The frame card widget
        """
        card = QFrame()
        card.setFixedSize(200, 250)
        card.setCursor(Qt.PointingHandCursor)

        # Store frame data on the card for click handler
        card.frame_path = frame_path
        card.frame_name = frame_name

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Thumbnail label
        thumbnail = QLabel()
        thumbnail.setFixedSize(180, 180)
        thumbnail.setStyleSheet("""
            QLabel {
                border: 3px solid #D4A574;
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)

        # Load and scale image
        if os.path.exists(frame_path):
            pixmap = QPixmap(frame_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    180, 180,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                thumbnail.setPixmap(scaled_pixmap)
            else:
                # Show placeholder text for corrupted image
                thumbnail.setText("⚠")
                thumbnail.setStyleSheet("""
                    QLabel {
                        border: 3px solid #444444;
                        border-radius: 8px;
                        background-color: #222222;
                        color: #FFC0CB;
                        font-size: 48px;
                    }
                """)

        # Frame name label
        name_label = QLabel(frame_name.replace('_', ' ').title())
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 14px;
                font-weight: bold;
                background-color: transparent;
            }
        """)

        layout.addWidget(thumbnail, alignment=Qt.AlignCenter)
        layout.addWidget(name_label, alignment=Qt.AlignCenter)
        card.setLayout(layout)

        # Apply card styling
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.4);
                border: 3px solid #D4A574;
                border-radius: 12px;
            }
        """)

        # Add hover effect using enter/leave events
        def enter_event(event):
            card.setStyleSheet("""
                QFrame {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #FFE4C4,
                        stop:1 #FFDAB9
                    );
                    border: 3px solid #1A0A00;
                    border-radius: 12px;
                }
            """)
            thumbnail.setStyleSheet("""
                QLabel {
                    border: 3px solid #1A0A00;
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 0.5);
                }
            """)
            card.enterEvent = lambda e: None  # Prevent recursive calls

        def leave_event(event):
            card.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.4);
                    border: 3px solid #D4A574;
                    border-radius: 12px;
                }
            """)
            thumbnail.setStyleSheet("""
                QLabel {
                    border: 3px solid #D4A574;
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 0.4);
                }
            """)
            card.leaveEvent = lambda e: None  # Prevent recursive calls

        # Override enter/leave events for hover effect
        original_enter = card.enterEvent
        original_leave = card.leaveEvent

        def on_enter(event):
            enter_event(event)
            original_enter(event)

        def on_leave(event):
            leave_event(event)
            original_leave(event)

        card.enterEvent = on_enter
        card.leaveEvent = on_leave

        # Add click handler
        def mouse_press_event(event):
            # Set selected frame and accept dialog
            self.selected_frame = frame_path
            self.selected_name = frame_name
            self.accept()

        card.mousePressEvent = mouse_press_event

        return card

    def get_selected_frame(self):
        """
        Get the selected frame information.

        Returns:
            tuple: (frame_path, frame_name) if a frame was selected,
                   (None, None) if dialog was cancelled

        Example:
            frame_path, frame_name = dialog.get_selected_frame()
            if frame_path:
                print(f"Selected: {frame_name}")
        """
        return (self.selected_frame, self.selected_name)
