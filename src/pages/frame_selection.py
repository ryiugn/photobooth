"""
Frame Selection Page (Page 1)
Allows users to choose a photo frame before capturing photos.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
import os
from pathlib import Path


class FrameCard(QFrame):
    """Clickable card displaying a frame thumbnail."""

    clicked = pyqtSignal(int)

    def __init__(self, frame_path, frame_name, index):
        super().__init__()
        self.frame_path = frame_path
        self.frame_name = frame_name
        self.index = index
        self.selected = False

        self.setFixedSize(200, 250)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Thumbnail
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(180, 180)
        self.thumbnail.setStyleSheet("""
            QLabel {
                border: 3px solid #444444;
                border-radius: 8px;
                background-color: #222222;
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
                self.thumbnail.setPixmap(scaled_pixmap)
            else:
                # Show placeholder text for corrupted image
                self.thumbnail.setText("⚠️")
                self.thumbnail.setStyleSheet("""
                    QLabel {
                        border: 3px solid #444444;
                        border-radius: 8px;
                        background-color: #222222;
                        color: #FFC0CB;
                        font-size: 48px;
                    }
                """)

        # Frame name
        self.name_label = QLabel(frame_name.replace('_', ' ').title())
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                background-color: transparent;
            }
        """)

        layout.addWidget(self.thumbnail, alignment=Qt.AlignCenter)
        layout.addWidget(self.name_label, alignment=Qt.AlignCenter)
        self.setLayout(layout)

        # Initial styling
        self._update_style()

    def _update_style(self):
        """Update card styling based on selection state."""
        if self.selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFC0CB;
                    border: 3px solid #FFC0CB;
                    border-radius: 12px;
                }
            """)
            self.thumbnail.setStyleSheet("""
                QLabel {
                    border: 3px solid #FFC0CB;
                    border-radius: 8px;
                    background-color: #222222;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #3A3A3A;
                    border: 3px solid #444444;
                    border-radius: 12px;
                }
            """)
            self.thumbnail.setStyleSheet("""
                QLabel {
                    border: 3px solid #444444;
                    border-radius: 8px;
                    background-color: #222222;
                }
            """)

    def set_selected(self, selected):
        """Set selection state and update styling."""
        self.selected = selected
        self._update_style()

    def mousePressEvent(self, event):
        """Handle mouse click to emit clicked signal."""
        self.clicked.emit(self.index)
        super().mousePressEvent(event)


class FrameSelectionPage(QWidget):
    """Page 1 - Frame Selection Screen"""

    # Signal emitted when user selects a frame and clicks continue
    frame_selected = pyqtSignal(str)  # Emits frame path

    def __init__(self, frames_dir="project_files/frames"):
        super().__init__()

        self.frames_dir = frames_dir
        self.frames = []  # List of (path, name) tuples
        self.selected_frame = None  # Currently selected frame path
        self.cards = []  # FrameCard widgets

        self._load_frames()
        self._setup_ui()

    def _load_frames(self):
        """Load frame images from the frames directory."""
        frames_path = Path(self.frames_dir)

        # Create directory if it doesn't exist
        if not frames_path.exists():
            frames_path.mkdir(parents=True, exist_ok=True)

        # Support .png, .jpg, .jpeg
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            for frame_file in frames_path.glob(ext):
                self.frames.append((str(frame_file), frame_file.stem))

        # Sort alphabetically by name
        self.frames.sort(key=lambda x: x[1])

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Title
        title = QLabel("CHOOSE YOUR FRAME")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #FFC0CB;
                font-size: 36px;
                font-weight: bold;
                background-color: transparent;
                padding: 20px;
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
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        # Grid layout for frame cards
        grid = QGridLayout()
        grid.setSpacing(20)
        grid.setContentsMargins(20, 20, 20, 20)

        # Create frame cards
        cols = 3  # Number of columns in grid
        for idx, (frame_path, frame_name) in enumerate(self.frames):
            card = FrameCard(frame_path, frame_name, idx)
            card.clicked.connect(self._on_card_clicked)
            self.cards.append(card)

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

        # Continue button
        self.continue_button = QPushButton("START PHOTO SESSION")
        self.continue_button.setFixedSize(300, 60)
        self.continue_button.setEnabled(False)  # Disabled until frame selected
        self.continue_button.setCursor(Qt.PointingHandCursor)
        self.continue_button.setStyleSheet("""
            QPushButton {
                background-color: #FFC0CB;
                color: #333333;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background-color: #FFB0C0;
            }
            QPushButton:pressed {
                background-color: #FFA0B0;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
                cursor: default;
            }
        """)
        self.continue_button.clicked.connect(self.on_continue)
        layout.addWidget(self.continue_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

        # Apply page background
        self.setStyleSheet("background-color: #333333;")

    def _on_card_clicked(self, index):
        """Handle frame card click."""
        self.select_frame(index)

    def select_frame(self, index):
        """Select a frame by index."""
        if 0 <= index < len(self.frames):
            # Deselect all cards
            for card in self.cards:
                card.set_selected(False)

            # Select clicked card
            self.cards[index].set_selected(True)

            # Store selected frame path
            self.selected_frame = self.frames[index][0]

            # Enable continue button
            self.continue_button.setEnabled(True)

    def on_continue(self):
        """Handle continue button click."""
        if self.selected_frame:
            self.frame_selected.emit(self.selected_frame)
