# Per-Photo Frame Selection with Templates Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow users to select a different frame for each of the 4 photos in a photostrip, and save/load frame combinations as templates.

**Architecture:**
- Page 1 (Frame Selection) redesigned with 4 frame slot cards
- New Page 1.5 (Template Manager) for CRUD operations on templates
- CaptureDisplayPage modified to accept list of 4 frame paths
- Frame composer modified to apply different frames per photo
- Templates stored as JSON files in `project_files/templates/`

**Tech Stack:**
- PyQt5 for UI components
- JSON for template persistence
- pathlib for file operations
- dataclasses for data models

---

### Task 1: Create Template Data Model and Storage

**Files:**
- Create: `src/template_storage.py`
- Test: `tests/test_template_storage.py`

**Step 1: Create template dataclass**

```python
# src/template_storage.py
from dataclasses import dataclass
from datetime import datetime
from typing import List
from pathlib import Path

@dataclass
class Template:
    """Represents a saved frame combination template."""
    name: str
    frame_paths: List[str]  # Exactly 4 frame paths
    created: str  # ISO format timestamp

    def __post_init__(self):
        if len(self.frame_paths) != 4:
            raise ValueError("Template must have exactly 4 frames")
```

**Step 2: Create TemplateStorage class**

```python
class TemplateStorage:
    """Manages template CRUD operations."""

    def __init__(self, templates_dir="project_files/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def save(self, template: Template) -> str:
        """Save template to JSON file. Returns filename."""
        # Use safe filename from template name
        safe_name = "".join(c if c.isalnum() else "_" for c in template.name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.json"
        filepath = self.templates_dir / filename

        import json
        data = {
            "name": template.name,
            "frames": template.frame_paths,
            "created": template.created
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        return str(filepath)

    def load_all(self) -> List[Template]:
        """Load all templates from directory."""
        templates = []
        import json

        for json_file in self.templates_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                templates.append(Template(
                    name=data["name"],
                    frame_paths=data["frames"],
                    created=data.get("created", "")
                ))
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip corrupted files
                continue

        # Sort by created date (newest first)
        templates.sort(key=lambda t: t.created, reverse=True)
        return templates

    def delete(self, template: Template):
        """Delete template file."""
        # Find and delete matching file
        for json_file in self.templates_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                if data.get("name") == template.name:
                    json_file.unlink()
                    break
            except:
                continue
```

**Step 3: Write tests**

```python
# tests/test_template_storage.py
import pytest
from pathlib import Path
import tempfile
import shutil
from src.template_storage import Template, TemplateStorage

@pytest.fixture
def temp_templates_dir():
    """Create temporary templates directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_template_requires_four_frames():
    """Template must have exactly 4 frames."""
    with pytest.raises(ValueError):
        Template(name="Test", frame_paths=["a.png", "b.png"], created="2026-01-27")

def test_save_and_load_template(temp_templates_dir):
    """Save template to file and load it back."""
    storage = TemplateStorage(templates_dir=temp_templates_dir)
    template = Template(
        name="My Mix",
        frame_paths=["f1.png", "f2.png", "f3.png", "f4.png"],
        created="2026-01-27T10:00:00"
    )

    storage.save(template)
    loaded = storage.load_all()

    assert len(loaded) == 1
    assert loaded[0].name == "My Mix"
    assert loaded[0].frame_paths == ["f1.png", "f2.png", "f3.png", "f4.png"]

def test_delete_template(temp_templates_dir):
    """Delete a template file."""
    storage = TemplateStorage(templates_dir=temp_templates_dir)
    template = Template(
        name="To Delete",
        frame_paths=["a.png", "b.png", "c.png", "d.png"],
        created="2026-01-27"
    )

    storage.save(template)
    assert len(storage.load_all()) == 1

    storage.delete(template)
    assert len(storage.load_all()) == 0
```

**Step 4: Run tests**

```bash
cd "C:\Users\dreka\OneDrive\Desktop\Y2S2\chai proj"
pytest tests/test_template_storage.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/template_storage.py tests/test_template_storage.py
git commit -m "feat: add template data model and storage"
```

---

### Task 2: Create FrameSlotCard Widget

**Files:**
- Create: `src/widgets/frame_slot_card.py`
- Modify: `src/pages/frame_selection.py`

**Step 1: Create FrameSlotCard widget**

```python
# src/widgets/frame_slot_card.py
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from pathlib import Path

class FrameSlotCard(QFrame):
    """A clickable card showing one frame slot for a photo."""

    clicked = pyqtSignal(int)  # Emits slot index when clicked

    def __init__(self, slot_index: int, frame_path: str = None):
        super().__init__()
        self.slot_index = slot_index
        self.frame_path = frame_path
        self.frame_name = None

        self.setFixedSize(180, 220)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Photo number label
        self.number_label = QLabel(f"PHOTO {slot_index + 1}")
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.number_label)

        # Thumbnail/placeholder
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(160, 160)
        self.thumbnail.setAlignment(Qt.AlignCenter)
        self.update_thumbnail()
        layout.addWidget(self.thumbnail)

        self.setLayout(layout)
        self._update_style()

    def set_frame(self, frame_path: str, frame_name: str):
        """Set the frame for this slot."""
        self.frame_path = frame_path
        self.frame_name = frame_name
        self.update_thumbnail()
        self._update_style()

    def clear_frame(self):
        """Clear the frame from this slot."""
        self.frame_path = None
        self.frame_name = None
        self.update_thumbnail()
        self._update_style()

    def update_thumbnail(self):
        """Update thumbnail display."""
        if self.frame_path and Path(self.frame_path).exists():
            pixmap = QPixmap(self.frame_path)
            scaled = pixmap.scaled(
                160, 160,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.thumbnail.setPixmap(scaled)
        else:
            # Show placeholder
            self.thumbnail.setText("+")
            self.thumbnail.setStyleSheet("""
                QLabel {
                    background-color: rgba(200, 180, 160, 0.5);
                    border: 3px dashed #D4A574;
                    border-radius: 8px;
                    font-size: 48px;
                    color: #1A0A00;
                }
            """)

    def _update_style(self):
        """Update card styling based on selection state."""
        if self.frame_path:
            # Has frame selected
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.6);
                    border: 3px solid #4CAF50;
                    border-radius: 12px;
                }
            """)
        else:
            # Empty slot
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.4);
                    border: 3px solid #D4A574;
                    border-radius: 12px;
                }
            """)

    def mousePressEvent(self, event):
        """Handle click to open frame picker."""
        self.clicked.emit(self.slot_index)
        super().mousePressEvent(event)
```

**Step 2: Test manually**

Create a simple test script to verify the widget displays correctly:

```python
# test_frame_slot.py
from PyQt5.QtWidgets import QApplication
from src.widgets.frame_slot_card import FrameSlotCard
import sys

app = QApplication(sys.argv)

# Test empty slot
slot1 = FrameSlotCard(0)
slot1.show()

# Test with frame
slot2 = FrameSlotCard(1, frame_path="project_files/frames/frame_classic.png")
slot2.show()

sys.exit(app.exec_())
```

Run: `python test_frame_slot.py`

**Step 3: Commit**

```bash
git add src/widgets/frame_slot_card.py
git commit -m "feat: add FrameSlotCard widget"
```

---

### Task 3: Create FramePickerDialog

**Files:**
- Create: `src/widgets/frame_picker_dialog.py`

**Step 1: Create the dialog**

```python
# src/widgets/frame_picker_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QScrollArea,
                             QGridLayout, QFrame, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from pathlib import Path

class FramePickerDialog(QDialog):
    """Modal dialog for selecting a frame."""

    def __init__(self, frames_dir="project_files/frames", parent=None):
        super().__init__(parent)
        self.frames_dir = frames_dir
        self.selected_frame = None
        self.selected_name = None
        self.frames = self._load_frames()

        self.setWindowTitle("Select a Frame")
        self.setModal(True)
        self.setFixedSize(800, 600)

        self._setup_ui()

    def _load_frames(self):
        """Load available frames."""
        frames = []
        frames_path = Path(self.frames_dir)

        for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
            for frame_file in frames_path.glob(ext):
                frames.append((str(frame_file), frame_file.stem))

        frames.sort(key=lambda x: x[1])
        return frames

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("CHOOSE A FRAME")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title)

        # Scroll area for frame grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        scroll_widget = QFrame()
        grid = QGridLayout()
        grid.setSpacing(15)

        # Create frame cards
        cols = 3
        for idx, (frame_path, frame_name) in enumerate(self.frames):
            card = self._create_frame_card(frame_path, frame_name, idx)
            row = idx // cols
            col = idx % cols
            grid.addWidget(card, row, col)

        scroll_widget.setLayout(grid)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Cancel button
        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setFixedHeight(50)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        self.setLayout(layout)

        # Apply background
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFF8DC,
                    stop:1 #FFDAB9
                );
            }
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
                border-radius: 8px;
            }
        """)

    def _create_frame_card(self, frame_path, frame_name, index):
        """Create clickable frame card."""
        card = QFrame()
        card.setFixedSize(200, 200)
        card.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Thumbnail
        thumb = QLabel()
        thumb.setFixedSize(180, 180)
        if Path(frame_path).exists():
            pixmap = QPixmap(frame_path)
            scaled = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumb.setPixmap(scaled)

        layout.addWidget(thumb)
        card.setLayout(layout)

        # Click handler
        def on_click():
            self.selected_frame = frame_path
            self.selected_name = frame_name
            self.accept()

        card.mousePressEvent = lambda e: on_click()

        # Hover effect
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.4);
                border: 2px solid #D4A574;
                border-radius: 10px;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.6);
                border: 2px solid #FFC0CB;
            }
        """)

        return card

    def get_selected_frame(self):
        """Return (frame_path, frame_name) tuple."""
        return self.selected_frame, self.selected_name
```

**Step 2: Commit**

```bash
git add src/widgets/frame_picker_dialog.py
git commit -m "feat: add FramePickerDialog for frame selection"
```

---

### Task 4: Redesign FrameSelectionPage with 4 Slots

**Files:**
- Modify: `src/pages/frame_selection.py`

**Step 1: Update imports and signals**

```python
# At top of frame_selection.py
from src.widgets.frame_slot_card import FrameSlotCard
from src.widgets.frame_picker_dialog import FramePickerDialog
```

**Step 2: Update __init__ to use list of 4 frames**

```python
def __init__(self, frames_dir="project_files/frames"):
    super().__init__()

    self.frames_dir = frames_dir
    self.frames = []  # List of (path, name) tuples
    self.selected_frames = [None, None, None, None]  # 4 slots
    self.cards = []  # FrameCard widgets (old gallery)

    # NEW: Frame slot cards
    self.frame_slots = []  # FrameSlotCard widgets

    self._load_frames()
    self._setup_ui()
```

**Step 3: Replace UI layout**

Find the `_setup_ui` method and replace the frame grid section with slot cards:

```python
def _setup_ui(self):
    """Setup the user interface with 4 frame slots."""
    layout = QVBoxLayout()
    layout.setContentsMargins(40, 40, 40, 40)
    layout.setSpacing(30)

    # Back button (unchanged)
    self.back_button = QPushButton("← BACK")
    # ... existing back button code ...
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
        }
    """)
    layout.addWidget(title)

    # NEW: 4 Frame slots in horizontal layout
    slots_container = QHBoxLayout()
    slots_container.setSpacing(20)

    for i in range(4):
        slot = FrameSlotCard(i)
        slot.clicked.connect(self._on_slot_clicked)
        self.frame_slots.append(slot)
        slots_container.addWidget(slot)

    # Add centering
    layout.addStretch()
    layout.addLayout(slots_container)
    layout.addStretch()

    # Button container
    button_container = QHBoxLayout()
    button_container.setSpacing(20)

    # NEW: Save Template button
    self.save_template_button = QPushButton("💾 SAVE AS TEMPLATE")
    self.save_template_button.setFixedSize(200, 60)
    self.save_template_button.setEnabled(False)
    self.save_template_button.setCursor(Qt.PointingHandCursor)
    self.save_template_button.clicked.connect(self._save_template)
    button_container.addWidget(self.save_template_button)

    # NEW: Load Template button
    self.load_template_button = QPushButton("📂 LOAD TEMPLATE")
    self.load_template_button.setFixedSize(200, 60)
    self.load_template_button.setCursor(Qt.PointingHandCursor)
    self.load_template_button.clicked.connect(self._load_template)
    button_container.addWidget(self.load_template_button)

    # Upload button (keep existing)
    self.upload_button = QPushButton("⬆ UPLOAD FRAMES")
    self.upload_button.setFixedSize(200, 60)
    self.upload_button.setCursor(Qt.PointingHandCursor)
    self.upload_button.clicked.connect(self.upload_frame)
    button_container.addWidget(self.upload_button)

    # Continue button (updated)
    self.continue_button = QPushButton("START PHOTO SESSION")
    self.continue_button.setFixedSize(250, 60)
    self.continue_button.setEnabled(False)
    self.continue_button.setCursor(Qt.PointingHandCursor)
    self.continue_button.clicked.connect(self.on_continue)
    button_container.addWidget(self.continue_button)

    layout.addLayout(button_container)
    self.setLayout(layout)

    # Apply styling
    button_style = """
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
        QPushButton:disabled {
            background-color: rgba(200, 180, 160, 0.5);
            color: rgba(26, 10, 0, 0.5);
            border: 2px solid rgba(26, 10, 0, 0.3);
        }
    """
    self.save_template_button.setStyleSheet(button_style.replace("#FFE4C4", "#E3F2FD").replace("#FFDAB9", "#BBDEFB"))
    self.load_template_button.setStyleSheet(button_style)
    self.upload_button.setStyleSheet(button_style)
    self.continue_button.setStyleSheet(button_style.replace("#FFE4C4", "#FFC0CB").replace("#FFDAB9", "#FFB6C1"))

    # Background
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
```

**Step 4: Add slot click handler**

```python
def _on_slot_clicked(self, slot_index: int):
    """Handle frame slot click - open frame picker."""
    dialog = FramePickerDialog(frames_dir=self.frames_dir, parent=self)

    if dialog.exec_() == QDialog.Accepted:
        frame_path, frame_name = dialog.get_selected_frame()
        if frame_path:
            self.selected_frames[slot_index] = (frame_path, frame_name)
            self.frame_slots[slot_index].set_frame(frame_path, frame_name)
            self._update_buttons()
```

**Step 5: Update button state logic**

```python
def _update_buttons(self):
    """Enable/disable buttons based on selection state."""
    all_selected = all(f is not None for f in self.selected_frames)
    self.continue_button.setEnabled(all_selected)
    self.save_template_button.setEnabled(all_selected)
```

**Step 6: Update on_continue to emit list**

```python
def on_continue(self):
    """Handle continue button click - emit all 4 frames."""
    if all(self.selected_frames):
        # Emit list of (path, name) tuples
        self.frame_selected.emit(self.selected_frames)  # Changed from single frame
```

**Step 7: Add template handlers**

```python
def _save_template(self):
    """Save current frame selection as template."""
    if not all(self.selected_frames):
        return

    from PyQt5.QtWidgets import QInputDialog
    from src.template_storage import Template, TemplateStorage
    from datetime import datetime

    # Get template name from user
    name, ok = QInputDialog.getText(self, "Save Template", "Enter template name:")
    if ok and name:
        storage = TemplateStorage()
        template = Template(
            name=name,
            frame_paths=[f[0] for f in self.selected_frames],
            created=datetime.now().isoformat()
        )
        storage.save(template)
        QMessageBox.information(self, "Template Saved", f"Template '{name}' saved successfully!")

def _load_template(self):
    """Open template manager dialog."""
    from src.pages.template_manager import TemplateManagerPage
    # This will be implemented in Task 5
    # For now, placeholder
    QMessageBox.information(self, "Coming Soon", "Template manager will be implemented next!")
```

**Step 8: Commit**

```bash
git add src/pages/frame_selection.py
git commit -m "feat: redesign frame selection with 4 slots"
```

---

### Task 5: Create TemplateManagerPage

**Files:**
- Create: `src/pages/template_manager.py`

**Step 1: Create the page**

```python
# src/pages/template_manager.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QFrame, QMessageBox,
                             QGridLayout, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from pathlib import Path

from src.template_storage import Template, TemplateStorage

class TemplateManagerPage(QWidget):
    """Page for managing frame templates."""

    template_selected = pyqtSignal(list)  # Emits list of 4 frame paths
    go_back = pyqtSignal()

    def __init__(self, templates_dir="project_files/templates"):
        super().__init__()

        self.templates_dir = templates_dir
        self.storage = TemplateStorage(templates_dir)
        self.templates = []
        self.selected_template = None

        self._load_templates()
        self._setup_ui()

    def _load_templates(self):
        """Load all templates from storage."""
        self.templates = self.storage.load_all()

    def _setup_ui(self):
        """Setup template manager UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left side: Template list
        left_panel = QVBoxLayout()
        left_panel.setSpacing(15)

        # Title
        title = QLabel("TEMPLATES")
        title.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 28px;
                font-weight: bold;
            }
        """)
        left_panel.addWidget(title)

        # Template list
        self.template_list = QListWidget()
        self.template_list.setIconSize(__import__('PyQt5.QtCore').QSize(300, 80))
        self.template_list.itemClicked.connect(self._on_template_selected)
        self._populate_template_list()
        left_panel.addWidget(self.template_list)

        # Delete button
        self.delete_button = QPushButton("🗑 DELETE TEMPLATE")
        self.delete_button.setFixedHeight(50)
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._delete_template)
        left_panel.addWidget(self.delete_button)

        # Cancel button
        cancel_btn = QPushButton("← BACK")
        cancel_btn.setFixedHeight(50)
        cancel_btn.clicked.connect(self.go_back.emit)
        left_panel.addWidget(cancel_btn)

        # Right side: Preview
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)

        # Preview title
        preview_title = QLabel("PREVIEW")
        preview_title.setStyleSheet("""
            QLabel {
                color: #1A0A00;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        right_panel.addWidget(preview_title)

        # Preview area
        self.preview_area = QFrame()
        self.preview_area.setFixedSize(400, 600)
        self.preview_area.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.5);
                border: 3px solid #D4A574;
                border-radius: 12px;
            }
        """)
        right_panel.addWidget(self.preview_area, alignment=Qt.AlignCenter)

        # Use template button
        self.use_button = QPushButton("USE THIS TEMPLATE")
        self.use_button.setFixedHeight(60)
        self.use_button.setEnabled(False)
        self.use_button.clicked.connect(self._use_template)
        right_panel.addWidget(self.use_button)

        # Add panels to main layout
        layout.addLayout(left_panel, stretch=1)
        layout.addLayout(right_panel, stretch=1)

        self.setLayout(layout)

        # Background
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFF8DC,
                    stop:1 #FFDAB9
                );
            }
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
                border-radius: 8px;
            }
            QListWidget {
                background-color: rgba(255, 255, 255, 0.6);
                border: 2px solid #D4A574;
                border-radius: 8px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #D4A574;
            }
            QListWidget::item:selected {
                background-color: #FFC0CB;
            }
        """)

    def _populate_template_list(self):
        """Populate list widget with templates."""
        self.template_list.clear()

        for template in self.templates:
            item = QListWidgetItem(f"{template.name}\nCreated: {template.created[:10]}")
            item.setData(Qt.UserRole, template)
            self.template_list.addItem(item)

    def _on_template_selected(self, item):
        """Handle template selection from list."""
        template = item.data(Qt.UserRole)
        self.selected_template = template
        self.delete_button.setEnabled(True)
        self.use_button.setEnabled(True)
        self._update_preview(template)

    def _update_preview(self, template: Template):
        """Update preview area with template frames."""
        # Clear existing layout
        layout = self.preview_area.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            layout = QVBoxLayout()
            layout.setSpacing(10)

        # Add 4 frame previews
        for i, frame_path in enumerate(template.frame_paths):
            if Path(frame_path).exists():
                label = QLabel()
                label.setFixedSize(350, 80)
                pixmap = QPixmap(frame_path)
                scaled = pixmap.scaled(350, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(scaled)
                layout.addWidget(label, alignment=Qt.AlignCenter)
            else:
                # Missing frame placeholder
                label = QLabel(f"Frame {i+1}: Missing")
                label.setStyleSheet("color: red;")
                layout.addWidget(label)

        self.preview_area.setLayout(layout)

    def _delete_template(self):
        """Delete selected template."""
        if not self.selected_template:
            return

        reply = QMessageBox.question(
            self,
            "Delete Template",
            f"Are you sure you want to delete '{self.selected_template.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.storage.delete(self.selected_template)
            self._load_templates()
            self._populate_template_list()
            self.selected_template = None
            self.delete_button.setEnabled(False)
            self.use_button.setEnabled(False)

    def _use_template(self):
        """Emit selected template frames."""
        if self.selected_template:
            self.template_selected.emit(self.selected_template.frame_paths)
            self.go_back.emit()
```

**Step 2: Commit**

```bash
git add src/pages/template_manager.py
git commit -m "feat: add template manager page"
```

---

### Task 6: Integrate TemplateManager into FrameSelectionPage

**Files:**
- Modify: `src/pages/frame_selection.py`
- Modify: `src/main.py`

**Step 1: Update frame_selection.py template handler**

Replace the placeholder `_load_template` method:

```python
def _load_template(self):
    """Navigate to template manager page."""
    # This signal will be connected in main.py
    self.open_template_manager.emit()
```

Add the signal to class:

```python
class FrameSelectionPage(QWidget):
    frame_selected = pyqtSignal(list)  # Now emits list of 4 frames
    go_back = pyqtSignal()
    open_template_manager = pyqtSignal()  # NEW
```

**Step 2: Update main.py to add template manager page**

```python
# In main.py imports
from src.pages.template_manager import TemplateManagerPage

# In setup_pages method, after frame_selection page:
# Page 1.5: Template Manager (created when needed)
self.pages["template_manager"] = None
```

**Step 3: Connect signals in connect_signals method**

```python
# Frame Selection → Template Manager
self.pages["frame_selection"].open_template_manager.connect(self.go_to_template_manager)

# Template Manager → Frame Selection
# Will be connected when page is created
```

**Step 4: Add navigation methods**

```python
def go_to_template_manager(self):
    """Navigate to template manager page."""
    from src.pages.template_manager import TemplateManagerPage

    template_page = TemplateManagerPage()

    # Clean up old if exists
    if self.pages["template_manager"] is not None:
        self.removeWidget(self.pages["template_manager"])

    # Add new page
    self.pages["template_manager"] = template_page
    self.addWidget(template_page)

    # Connect signals
    template_page.template_selected.connect(self._on_template_selected)
    template_page.go_back.connect(self.go_to_frame_selection)

    # Navigate
    self.setCurrentWidget(template_page)

def _on_template_selected(self, frame_paths: list):
    """Handle template selection - apply to frame selection page."""
    # Update frame selection page with template frames
    frame_page = self.pages["frame_selection"]

    from pathlib import Path
    for i, frame_path in enumerate(frame_paths):
        if Path(frame_path).exists():
            frame_name = Path(frame_path).stem
            frame_page.selected_frames[i] = (frame_path, frame_name)
            frame_page.frame_slots[i].set_frame(frame_path, frame_name)

    frame_page._update_buttons()
```

**Step 5: Commit**

```bash
git add src/pages/frame_selection.py src/main.py
git commit -m "feat: integrate template manager into navigation flow"
```

---

### Task 7: Modify CaptureDisplayPage for Multiple Frames

**Files:**
- Modify: `src/pages/capture_display.py`

**Step 1: Update __init__ signature**

```python
def __init__(self, frame_paths: list, output_dir: str = "project_files/captured_images", photos_per_strip: int = 4):
    """Initialize with list of 4 frame paths."""
    super().__init__()

    print(f"[DEBUG] CaptureDisplayPage.__init__ called with {len(frame_paths)} frames")

    if len(frame_paths) != 4:
        raise ValueError(f"Expected 4 frame paths, got {len(frame_paths)}")

    self.frame_paths = frame_paths  # Store list of 4 paths
    self.output_dir = Path(output_dir)
    self.output_dir.mkdir(parents=True, exist_ok=True)

    # Rest of init unchanged...
```

**Step 2: Update capture_photo to use correct frame**

```python
def capture_photo(self):
    """Capture a photo with current photo index's frame."""
    if not self.camera_handler:
        QMessageBox.warning(self, "Error", "Camera not available")
        return

    try:
        # Stop camera feed
        self.feed_timer.stop()

        # Capture photo from camera (BGR format)
        self.current_capture = self.camera_handler.capture_photo()

        # Apply frame overlay for CURRENT photo index
        current_frame = self.frame_paths[self.current_photo_index]
        framed_photo = apply_frame(self.current_capture, current_frame)

        # Display preview
        self.display_photo_preview(framed_photo)

        # Switch to preview mode
        self.stacked_widget.setCurrentWidget(self.preview_widget)

        # Re-enable capture button
        self.capture_button.setEnabled(True)

    except RuntimeError as e:
        QMessageBox.critical(self, "Error", f"Failed to capture photo: {str(e)}")
        self.retake_current_photo()
        self.capture_button.setEnabled(True)
```

**Step 3: Update progress indicator to show frame**

```python
def return_to_capture_mode(self):
    """Return to capture mode for next photo."""
    # Update progress label with current frame preview
    photo_num = self.current_photo_index + 1
    self.progress_label.setText(f"Photo {photo_num} of {self.photos_per_strip}")

    # Could add small thumbnail of current frame here
    current_frame = self.frame_paths[self.current_photo_index]
    # (Optional enhancement)

    # Clear preview
    self.preview_photo_label.clear()

    # Switch back to capture mode
    self.stacked_widget.setCurrentWidget(self.capture_widget)

    # Restart camera feed
    self.start_camera_feed()
```

**Step 4: Update compose_and_proceed**

```python
def compose_and_proceed(self):
    """Compose all captured photos with their respective frames."""
    if len(self.captured_photos) != self.photos_per_strip:
        QMessageBox.warning(self, "Error", f"Expected {self.photos_per_strip} photos, got {len(self.captured_photos)}")
        return

    try:
        # Import updated composer
        from src.frame_composer import compose_photostrip

        # Compose with list of frames
        self.final_image = compose_photostrip(self.captured_photos, self.frame_paths)

        # Navigate to Page 3
        self.photostrip_ready.emit(self.final_image)

    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to compose photostrip: {str(e)}")
        self.return_to_capture_mode()
```

**Step 5: Commit**

```bash
git add src/pages/capture_display.py
git commit -m "feat: support multiple frames in capture page"
```

---

### Task 8: Update Frame Composer for Per-Photo Frames

**Files:**
- Modify: `src/frame_composer.py`

**Step 1: Update compose_photostrip signature**

```python
def compose_photostrip(photos: list, frame_paths, gap: int = 20) -> Image.Image:
    """
    Compose multiple photos into a vertical photostrip with frame overlays.

    Args:
        photos: List of captured photos as numpy arrays (BGR format)
        frame_paths: Single frame path (str) or list of 4 frame paths
        gap: Gap between photos in pixels (default: 20)

    Returns:
        Composed PIL Image with all photos stacked vertically
    """
    if not photos:
        raise ValueError("No photos provided for composition")

    # Support both single frame (backward compat) and list of frames
    if isinstance(frame_paths, str):
        # Single frame for all photos
        frame_paths_list = [frame_paths] * len(photos)
    else:
        # List of frames (must match photo count)
        if len(frame_paths) != len(photos):
            raise ValueError(f"Number of frames ({len(frame_paths)}) must match number of photos ({len(photos)})")
        frame_paths_list = frame_paths

    # Convert all photos to PIL Images with their respective frames
    framed_photos = []
    for photo, frame_path in zip(photos, frame_paths_list):
        framed = apply_frame(photo, frame_path)
        framed_photos.append(framed)

    # Get dimensions from first framed photo
    first_width, first_height = framed_photos[0].size

    # Calculate strip dimensions
    strip_width = first_width
    strip_height = (first_height * len(framed_photos)) + (gap * (len(framed_photos) - 1))

    # Create new image for the strip
    photostrip = Image.new("RGB", (strip_width, strip_height))

    # Paste each photo vertically
    y_offset = 0
    for framed_photo in framed_photos:
        photostrip.paste(framed_photo, (0, y_offset))
        y_offset += first_height + gap

    return photostrip
```

**Step 2: Test backward compatibility**

```python
# test_composer.py
from src.frame_composer import compose_photostrip
import numpy as np

# Test single frame (old behavior)
# compose_photostrip(photos, "frame.png")  # Should work

# Test multiple frames (new behavior)
# compose_photostrip(photos, ["f1.png", "f2.png", "f3.png", "f4.png"])  # Should work
```

**Step 3: Commit**

```bash
git add src/frame_composer.py
git commit -m "feat: support per-photo frames in compose_photostrip"
```

---

### Task 9: Update main.py Navigation

**Files:**
- Modify: `src/main.py`

**Step 1: Update go_to_capture to handle list**

```python
def go_to_capture(self, frames_list: list):
    """
    Navigate to capture page with selected frames.

    Args:
        frames_list: List of 4 (frame_path, frame_name) tuples
    """
    print(f"[DEBUG] go_to_capture called with {len(frames_list)} frames")

    # Extract just the paths
    frame_paths = [f[0] for f in frames_list]

    # Create capture page with list of frame paths
    output_dir = "project_files/captured_images"
    config = LoginPage.load_config()
    photos_per_strip = config.get("photostrip", {}).get("photos_per_strip", 4)

    print(f"[DEBUG] Creating CaptureDisplayPage with frame_paths={frame_paths}")
    capture_page = CaptureDisplayPage(frame_paths=frame_paths, output_dir=output_dir, photos_per_strip=photos_per_strip)

    # Rest of method unchanged...
    print(f"[DEBUG] CaptureDisplayPage created successfully")

    # Clean up old capture page
    if self.pages["capture"] is not None:
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
```

**Step 2: Commit**

```bash
git add src/main.py
git commit -m "feat: pass frame list to capture page"
```

---

### Task 10: Final Testing and Polish

**Files:**
- Test entire flow

**Step 1: Test basic flow**

```bash
cd "C:\Users\dreka\OneDrive\Desktop\Y2S2\chai proj"
python src/main.py
```

Manual test:
1. Enter PIN: 1234
2. Select 4 different frames (one per slot)
3. Click START PHOTO SESSION
4. Take 4 photos
5. Verify each photo has correct frame
6. Verify final strip shows all 4 frames correctly

**Step 2: Test template save**

1. Select 4 frames
2. Click SAVE AS TEMPLATE
3. Enter name: "Test Template"
4. Verify success message

**Step 3: Test template load**

1. Click LOAD TEMPLATE
2. Select saved template
3. Click USE THIS TEMPLATE
4. Verify all 4 slots are filled correctly

**Step 4: Test template delete**

1. Click LOAD TEMPLATE
2. Select template
3. Click DELETE
4. Confirm deletion
5. Verify template removed from list

**Step 5: Edge cases**

- Test uploading new frames while slots are filled
- Test going back from capture page (should prompt to lose progress)
- Test retaking individual photos
- Test with missing frame files (template should show placeholders)

**Step 6: Polish UI**

- Add tooltips to buttons
- Ensure consistent styling
- Add loading states if needed
- Verify accessibility (keyboard navigation)

**Step 7: Update config.json**

Update default photos_per_strip to 4:

```json
{
  "photostrip": {
    "photos_per_strip": 4,
    "countdown_seconds": 3
  }
}
```

**Step 8: Final commit**

```bash
git add project_files/config.json
git commit -m "feat: complete per-photo frame selection with templates"
```

---

## Testing Checklist

- [ ] Can select 4 different frames
- [ ] START PHOTO SESSION button enables when all 4 selected
- [ ] Each photo captured uses correct frame
- [ ] Final photostrip shows all 4 frames correctly
- [ ] Can save frame selection as template
- [ ] Can load saved template
- [ ] Loaded template populates all 4 slots
- [ ] Can delete templates
- [ ] Back navigation works correctly
- [ ] Upload frames still works
- [ ] Templates persist across app restarts

---

## Implementation Complete

All tasks completed. The photobooth now supports:
- Selecting a different frame for each of the 4 photos
- Saving frame combinations as templates
- Loading saved templates
- Full template management (create, read, delete)
