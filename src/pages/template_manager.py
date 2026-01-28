"""
Template Manager Page
Allows users to view, select, and delete saved frame templates.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem,
                             QMessageBox, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from src.template_storage import Template, TemplateStorage
import os


class TemplateManagerPage(QWidget):
    """Template management screen for viewing, selecting, and deleting saved templates."""

    # Signals
    template_selected = pyqtSignal(list)  # Emits list of 4 frame paths
    go_back = pyqtSignal()  # Signal to return to previous page

    def __init__(self, parent=None):
        super().__init__(parent)

        # Storage for templates
        self.storage = TemplateStorage()
        self.templates = []  # List of Template objects
        self.current_template = None  # Currently selected template

        # Load templates and setup UI
        self._load_templates()
        self._setup_ui()

    def _load_templates(self):
        """Load all templates from TemplateStorage."""
        self.templates = self.storage.load_all()

    def _setup_ui(self):
        """Build the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Back button (positioned via parent)
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
        title = QLabel("TEMPLATE MANAGER")
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
        main_layout.addWidget(title)

        # Content container (left and right panels)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)

        # Left panel - Template list
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.6);
                border: 2px solid #D4A574;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)

        # Templates title
        templates_title = QLabel("TEMPLATES")
        templates_title.setAlignment(Qt.AlignCenter)
        templates_title.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 20px;
                font-weight: bold;
                background-color: transparent;
                padding: 10px;
            }
        """)
        left_layout.addWidget(templates_title)

        # Template list widget
        self.template_list = QListWidget()
        self.template_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(255, 255, 255, 0.8);
                border: 2px solid #D4A574;
                border-radius: 8px;
                font-size: 20px;
                color: #1A0A00;
                padding: 5px;
            }
            QListWidget::item {
                padding: 20px 15px;
                border-radius: 4px;
                margin: 2px;
                min-height: 70px;
            }
            QListWidget::item:selected {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFE4C4,
                    stop:1 #FFDAB9
                );
                border: 2px solid #1A0A00;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 228, 196, 0.5);
            }
        """)
        self.template_list.itemClicked.connect(self._on_template_selected)
        left_layout.addWidget(self.template_list)

        left_panel.setLayout(left_layout)
        content_layout.addWidget(left_panel, stretch=1)

        # Right panel - Preview area
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.6);
                border: 2px solid #D4A574;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(10)

        # Preview title
        preview_title = QLabel("PREVIEW")
        preview_title.setAlignment(Qt.AlignCenter)
        preview_title.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 20px;
                font-weight: bold;
                background-color: transparent;
                padding: 10px;
            }
        """)
        right_layout.addWidget(preview_title)

        # Preview area for 4 frame thumbnails
        self.preview_area = QWidget()
        self.preview_layout = QVBoxLayout()
        self.preview_layout.setSpacing(10)
        self.preview_area.setLayout(self.preview_layout)

        # Create 4 preview labels (initially empty)
        self.preview_labels = []
        for i in range(4):
            label = QLabel()
            label.setMinimumSize(150, 150)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    background-color: rgba(200, 180, 160, 0.3);
                    border: 2px dashed #D4A574;
                    border-radius: 8px;
                    color: #1A0A00;
                    font-size: 12px;
                }
            """)
            label.setText(f"Frame {i + 1}")
            self.preview_labels.append(label)
            self.preview_layout.addWidget(label)

        right_layout.addWidget(self.preview_area)
        right_panel.setLayout(right_layout)
        content_layout.addWidget(right_panel, stretch=1)

        main_layout.addLayout(content_layout, stretch=1)

        # Button container
        button_container = QHBoxLayout()
        button_container.setSpacing(20)
        button_container.addStretch()

        # Delete button
        self.delete_button = QPushButton("🗑 DELETE TEMPLATE")
        self.delete_button.setFixedSize(200, 60)
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._delete_template)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB6C1,
                    stop:1 #FFA0B0
                );
                color: #1A0A00;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #1A0A00;
                border-radius: 10px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFA0B0,
                    stop:1 #FF90A0
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF90A0,
                    stop:1 #FF8090
                );
            }
            QPushButton:disabled {
                background-color: rgba(200, 180, 160, 0.5);
                color: rgba(26, 10, 0, 0.5);
                border: 2px solid rgba(26, 10, 0, 0.3);
                cursor: default;
            }
        """)

        # Use Template button
        self.use_button = QPushButton("✓ USE TEMPLATE")
        self.use_button.setFixedSize(200, 60)
        self.use_button.setCursor(Qt.PointingHandCursor)
        self.use_button.setEnabled(False)
        self.use_button.clicked.connect(self._use_template)
        self.use_button.setStyleSheet("""
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
        """)

        button_container.addWidget(self.delete_button)
        button_container.addWidget(self.use_button)
        button_container.addStretch()

        main_layout.addLayout(button_container)

        self.setLayout(main_layout)

        # Apply seashell gradient background
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

        # Populate template list
        self._populate_template_list()

    def _populate_template_list(self):
        """Fill list widget with template names."""
        self.template_list.clear()

        if not self.templates:
            # Show message if no templates
            item = QListWidgetItem("No templates found")
            item.setFlags(Qt.NoItemFlags)
            self.template_list.addItem(item)
            return

        # Add each template to list
        for template in self.templates:
            item = QListWidgetItem(template.name)
            # Store template reference in item data
            item.setData(Qt.UserRole, template)
            self.template_list.addItem(item)

    def _on_template_selected(self, item):
        """Handle list selection - update preview and enable buttons."""
        # Get template from item data
        template = item.data(Qt.UserRole)

        if template is None:
            # "No templates found" item
            self.current_template = None
            self.delete_button.setEnabled(False)
            self.use_button.setEnabled(False)
            return

        self.current_template = template

        # Update preview
        self._update_preview(template)

        # Enable buttons
        self.delete_button.setEnabled(True)
        self.use_button.setEnabled(True)

    def _update_preview(self, template):
        """Show 4 frames in preview area.

        Args:
            template: Template object with frame_paths
        """
        if not template or len(template.frame_paths) != 4:
            return

        # Update each preview label
        for i, frame_path in enumerate(template.frame_paths):
            label = self.preview_labels[i]

            if os.path.exists(frame_path):
                # Load and display frame thumbnail
                pixmap = QPixmap(frame_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        150, 150,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    label.setPixmap(scaled_pixmap)
                    label.setStyleSheet("""
                        QLabel {
                            background-color: rgba(255, 255, 255, 0.8);
                            border: 2px solid #D4A574;
                            border-radius: 8px;
                        }
                    """)
                else:
                    # Invalid image file
                    label.setText(f"Frame {i + 1}\n(Error)")
                    label.clearPixmap()
            else:
                # File not found
                label.setText(f"Frame {i + 1}\n(Not found)")
                label.clearPixmap()

    def _delete_template(self):
        """Delete selected template with confirmation."""
        if not self.current_template:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Template?",
            f"Are you sure you want to delete template '{self.current_template.name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Delete from storage
            self.storage.delete(self.current_template)

            # Reload templates
            self._load_templates()

            # Repopulate list
            self._populate_template_list()

            # Clear preview and disable buttons
            self.current_template = None
            for label in self.preview_labels:
                label.clearPixmap()
                label.setText("Frame X")
                label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(200, 180, 160, 0.3);
                        border: 2px dashed #D4A574;
                        border-radius: 8px;
                        color: #1A0A00;
                        font-size: 12px;
                    }
                """)
            self.delete_button.setEnabled(False)
            self.use_button.setEnabled(False)

            QMessageBox.information(self, "Deleted", f"Template '{self.current_template.name}' has been deleted.")

    def _use_template(self):
        """Emit template_selected signal and go back."""
        if not self.current_template:
            return

        # Emit signal with list of 4 frame paths
        self.template_selected.emit(self.current_template.frame_paths)

        # Navigate back
        self.go_back.emit()

    def _on_back_clicked(self):
        """Handle back button click - emit go_back signal."""
        self.go_back.emit()

    def refresh_templates(self):
        """Refresh the template list from storage."""
        self._load_templates()
        self._populate_template_list()

    def resizeEvent(self, event):
        """Handle resize event - ensure back button stays in correct position."""
        super().resizeEvent(event)
        if hasattr(self, 'back_button'):
            self.back_button.move(20, 20)
            self.back_button.raise_()
