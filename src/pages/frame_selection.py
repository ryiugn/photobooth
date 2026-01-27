"""
Frame Selection Page (Page 1)
Allows users to choose a photo frame before capturing photos.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QGridLayout, QFrame,
                             QFileDialog, QMessageBox, QDialog, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from src.widgets.frame_slot_card import FrameSlotCard
from src.widgets.frame_picker_dialog import FramePickerDialog
import os
import shutil
from pathlib import Path
from datetime import datetime
import random
import string


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
                color: #1A0A00;
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
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #FFE4C4,
                        stop:1 #FFDAB9
                    );
                    border: 3px solid #1A0A00;
                    border-radius: 12px;
                }
            """)
            self.thumbnail.setStyleSheet("""
                QLabel {
                    border: 3px solid #1A0A00;
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 0.5);
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.4);
                    border: 3px solid #D4A574;
                    border-radius: 12px;
                }
            """)
            self.thumbnail.setStyleSheet("""
                QLabel {
                    border: 3px solid #D4A574;
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 0.4);
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

    # Signal emitted when user selects 4 frames and clicks continue
    frame_selected = pyqtSignal(list)  # Emits list of 4 (frame_path, frame_name) tuples
    go_back = pyqtSignal()  # Signal emitted when back button is clicked
    open_template_manager = pyqtSignal()  # Signal to open template manager

    def __init__(self, frames_dir="project_files/frames"):
        super().__init__()

        self.frames_dir = frames_dir
        self.frames = []  # List of (path, name) tuples
        self.selected_frames = [None, None, None, None]  # 4 slots for frames
        self.cards = []  # FrameCard widgets (for backward compatibility, not used in new UI)

        # NEW: Frame slot cards
        self.frame_slots = []  # FrameSlotCard widgets

        self._load_frames()
        self._setup_ui()

    def _load_frames(self):
        """Load frame images from the frames directory."""
        frames_path = Path(self.frames_dir)

        # Create directory if it doesn't exist
        if not frames_path.exists():
            frames_path.mkdir(parents=True, exist_ok=True)

        # Support .png, .jpg, .jpeg, .webp
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
            for frame_file in frames_path.glob(ext):
                self.frames.append((str(frame_file), frame_file.stem))

        # Sort alphabetically by name
        self.frames.sort(key=lambda x: x[1])

    def _setup_ui(self):
        """Set up the user interface with 4 frame slots."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Back button (top-left, positioned via parent)
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
        self.back_button.setParent(self)
        self.back_button.move(20, 20)

        # Title
        title = QLabel("CHOOSE YOUR FRAMES")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 36px;
                font-weight: bold;
                background-color: transparent;
                padding: 20px;
                text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8);
            }
        """)
        layout.addWidget(title)

        # Frame slots container (horizontal layout with 4 slots)
        slots_container = QHBoxLayout()
        slots_container.setSpacing(30)
        slots_container.addStretch()

        # Create 4 frame slot cards
        for i in range(4):
            slot = FrameSlotCard(slot_number=i + 1, parent=self)
            slot.slot_clicked.connect(lambda idx=i: self._on_slot_clicked(idx))
            self.frame_slots.append(slot)
            slots_container.addWidget(slot)

        slots_container.addStretch()
        layout.addLayout(slots_container, stretch=1)

        # Continue button
        self.continue_button = QPushButton("START PHOTO SESSION")
        self.continue_button.setFixedSize(300, 60)
        self.continue_button.setEnabled(False)  # Disabled until frame selected
        self.continue_button.setCursor(Qt.PointingHandCursor)
        self.continue_button.clicked.connect(self.on_continue)

        # Upload frame button
        self.upload_button = QPushButton("⬆ UPLOAD FRAMES")
        self.upload_button.setFixedSize(200, 60)
        self.upload_button.setCursor(Qt.PointingHandCursor)
        self.upload_button.clicked.connect(self.upload_frame)

        # Save template button
        self.save_template_button = QPushButton("💾 SAVE AS TEMPLATE")
        self.save_template_button.setFixedSize(220, 60)
        self.save_template_button.setCursor(Qt.PointingHandCursor)
        self.save_template_button.setEnabled(False)
        self.save_template_button.clicked.connect(self._save_template)

        # Load template button
        self.load_template_button = QPushButton("📂 LOAD TEMPLATE")
        self.load_template_button.setFixedSize(220, 60)
        self.load_template_button.setCursor(Qt.PointingHandCursor)
        self.load_template_button.clicked.connect(self._load_template)

        # Button style for main buttons
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
                cursor: default;
            }
        """
        self.continue_button.setStyleSheet(button_style)
        self.upload_button.setStyleSheet(button_style)

        # Blue accent style for template buttons
        template_button_style = """
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #87CEEB,
                    stop:1 #5FB4D9
                );
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #1A0A00;
                border-radius: 10px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5FB4D9,
                    stop:1 #4A9CC7
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4A9CC7,
                    stop:1 #3A7FA7
                );
            }
            QPushButton:disabled {
                background-color: rgba(135, 206, 235, 0.5);
                color: rgba(255, 255, 255, 0.5);
                border: 2px solid rgba(26, 10, 0, 0.3);
                cursor: default;
            }
        """
        self.save_template_button.setStyleSheet(template_button_style)
        self.load_template_button.setStyleSheet(template_button_style)

        # Button container
        button_container = QHBoxLayout()
        button_container.setSpacing(20)
        button_container.addStretch()
        button_container.addWidget(self.upload_button)
        button_container.addWidget(self.save_template_button)
        button_container.addWidget(self.load_template_button)
        button_container.addWidget(self.continue_button)
        button_container.addStretch()

        layout.addLayout(button_container)

        self.setLayout(layout)

        # Apply scallop seashell gradient background
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

    def _on_slot_clicked(self, slot_index: int):
        """Handle frame slot click - open frame picker."""
        dialog = FramePickerDialog(frames_dir=self.frames_dir, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            frame_path, frame_name = dialog.get_selected_frame()
            if frame_path:
                self.selected_frames[slot_index] = (frame_path, frame_name)
                self.frame_slots[slot_index].set_frame(frame_path, frame_name)
                self._update_buttons()

    def _update_buttons(self):
        """Enable/disable buttons based on selection state."""
        all_selected = all(f is not None for f in self.selected_frames)
        self.continue_button.setEnabled(all_selected)
        self.save_template_button.setEnabled(all_selected)

    def _save_template(self):
        """Save current frame selection as template."""
        if not all(self.selected_frames):
            return
        name, ok = QInputDialog.getText(self, "Save Template", "Enter template name:")
        if ok and name:
            from src.template_storage import Template, TemplateStorage
            storage = TemplateStorage()
            template = Template(
                name=name,
                frame_paths=[f[0] for f in self.selected_frames],
                created=datetime.now().isoformat()
            )
            storage.save(template)
            QMessageBox.information(self, "Template Saved", f"Template '{name}' saved successfully!")

    def _load_template(self):
        """Open template manager page."""
        self.open_template_manager.emit()

    def on_continue(self):
        """Handle continue button click - emit all 4 frames."""
        if all(self.selected_frames):
            self.frame_selected.emit(self.selected_frames)

    def _on_back_clicked(self):
        """Handle back button click - emit go_back signal."""
        self.go_back.emit()

    def upload_frame(self):
        """Handle upload frame button click - open file dialog and copy multiple frames."""
        # Open file dialog for multiple image selection
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Frame Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.PNG *.JPG *.JPEG *.WEBP);;All Files (*)"
        )

        if not file_paths:
            # User cancelled
            return

        # Ensure frames directory exists
        Path(self.frames_dir).mkdir(parents=True, exist_ok=True)

        uploaded_count = 0
        failed_files = []
        transparency_notes = []

        try:
            for file_path in file_paths:
                try:
                    # Verify file exists
                    source_path = Path(file_path)
                    if not source_path.exists():
                        failed_files.append(f"{source_path.name} (file not found)")
                        continue

                    # Generate unique filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    random_str = ''.join(random.choices(string.ascii_lowercase, k=6))
                    ext = source_path.suffix if source_path.suffix else '.png'
                    new_filename = f"custom_{timestamp}_{random_str}{ext}"
                    dest_path = Path(self.frames_dir) / new_filename

                    # Copy file to frames directory
                    shutil.copy2(source_path, dest_path)
                    uploaded_count += 1

                    # Check if image has transparency (for PNG)
                    if ext.lower() == '.png':
                        try:
                            from PIL import Image
                            img = Image.open(source_path)
                            if img.mode != 'RGBA' and 'transparency' not in img.info:
                                transparency_notes.append(new_filename)
                        except Exception:
                            # PIL not available or error checking transparency
                            pass

                except PermissionError:
                    failed_files.append(f"{source_path.name} (permission denied)")
                except Exception as e:
                    failed_files.append(f"{source_path.name} ({str(e)})")

            # Show summary message
            if uploaded_count > 0:
                message_parts = [f"Successfully uploaded {uploaded_count} frame(s)!"]

                if transparency_notes:
                    message_parts.append("\n\nNote: The following frames don't have transparent backgrounds:")
                    for filename in transparency_notes[:5]:  # Show max 5
                        message_parts.append(f"\n- {filename}")
                    if len(transparency_notes) > 5:
                        message_parts.append(f"\n... and {len(transparency_notes) - 5} more")
                    message_parts.append("\n\nFor best results, use PNG files with transparency.")

                if failed_files:
                    message_parts.append("\n\nFailed to upload:")
                    for failure in failed_files[:5]:  # Show max 5
                        message_parts.append(f"\n- {failure}")
                    if len(failed_files) > 5:
                        message_parts.append(f"\n... and {len(failed_files) - 5} more")

                QMessageBox.information(
                    self,
                    "Frames Uploaded",
                    ''.join(message_parts)
                )

                # Refresh frame list and rebuild UI
                self.refresh_frames()

            elif failed_files:
                # All files failed
                QMessageBox.critical(
                    self,
                    "Upload Failed",
                    f"Failed to upload any frames.\n\nErrors:\n" + "\n".join(f"- {f}" for f in failed_files[:5])
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to upload frames:\n{str(e)}"
            )

    def refresh_frames(self):
        """Refresh the frame list from directory."""
        # Store currently selected frames
        current_selection = self.selected_frames.copy()

        # Clear and reload frames list
        self.frames.clear()
        self._load_frames()

        # Update slots that have selected frames to refresh their thumbnails
        for i, (frame_path, frame_name) in enumerate(current_selection):
            if frame_path and os.path.exists(frame_path):
                # Frame still exists, keep it selected
                self.selected_frames[i] = (frame_path, frame_name)
            else:
                # Frame no longer exists, clear the slot
                self.selected_frames[i] = None

        # Update button states
        self._update_buttons()

    def resizeEvent(self, event):
        """Handle resize event - ensure back button stays in correct position."""
        super().resizeEvent(event)
        if hasattr(self, 'back_button'):
            self.back_button.move(20, 20)
            self.back_button.raise_()
