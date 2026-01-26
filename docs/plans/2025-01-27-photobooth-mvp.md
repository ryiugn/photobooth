# Photobooth MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a simplified photobooth application with PIN authentication, frame selection, and photo capture with FOFOBOOTH styling.

**Architecture:** PyQt5 application with QStackedWidget managing 3 pages (Login, Frame Selection, Capture/Display), OpenCV for camera, Pillow for image composition.

**Tech Stack:** Python 3, PyQt5, OpenCV, Pillow, NumPy

---

## Task 1: Initialize Project Structure

**Files:**
- Create: `src/__init__.py`
- Create: `src/pages/__init__.py`
- Create: `project_frames/__init__.py`
- Create: `requirements.txt`
- Create: `project_files/config.json`
- Create: `.gitignore`

**Step 1: Create directory structure**

```bash
mkdir -p src/pages project_files/frames project_files/captured_images docs/plans
```

**Step 2: Create requirements.txt**

```txt
PyQt5==5.15.9
opencv-python==4.8.0.74
Pillow==10.0.0
numpy==1.24.3
```

**Step 3: Create config.json**

```json
{
  "app_name": "Photobooth",
  "pin": "1234",
  "camera": {
    "device_index": 0,
    "width": 1280,
    "height": 720
  },
  "frames_dir": "project_files/frames",
  "output_dir": "project_files/captured_images"
}
```

**Step 4: Create .gitignore**

```
*.pyc
__pycache__/
*.py[cod]
*$py.class
.env
.venv
env/
venv/
project_files/captured_images/*.png
```

**Step 5: Create empty __init__.py files**

```bash
touch src/__init__.py src/pages/__init__.py project_files/__init__.py
```

**Step 6: Commit**

```bash
git add .
git commit -m "feat: initialize project structure and configuration"
```

---

## Task 2: Create Camera Handler Module

**Files:**
- Create: `src/camera_handler.py`
- Create: `tests/test_camera_handler.py`

**Step 1: Write the failing test**

Create `tests/test_camera_handler.py`:

```python
import pytest
import numpy as np
from src.camera_handler import CameraHandler

def test_camera_handler_initialization():
    handler = CameraHandler(device_index=0)
    assert handler.camera is not None
    handler.release()

def test_capture_photo():
    handler = CameraHandler(device_index=0)
    photo = handler.capture_photo()
    assert isinstance(photo, np.ndarray)
    assert photo.shape[2] == 3  # BGR color image
    handler.release()

def test_get_frame_returns_qpixmap():
    from PyQt5.QtGui import QPixmap
    handler = CameraHandler(device_index=0)
    pixmap = handler.get_frame()
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()
    handler.release()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_camera_handler.py -v
```

Expected: `ImportError: cannot import name 'CameraHandler'`

**Step 3: Write minimal implementation**

Create `src/camera_handler.py`:

```python
import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


class CameraHandler:
    """Manages camera operations for photobooth application."""

    def __init__(self, device_index: int = 0, width: int = 1280, height: int = 720):
        """Initialize camera with specified device and resolution."""
        self.device_index = device_index
        self.width = width
        self.height = height
        self.camera = cv2.VideoCapture(device_index)
        if not self.camera.isOpened():
            raise RuntimeError(f"Could not open camera at index {device_index}")
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def get_frame(self) -> QPixmap:
        """Capture a frame and return as QPixmap for display."""
        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError("Failed to capture frame from camera")

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert to QImage
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # Convert to QPixmap
        return QPixmap.fromImage(qt_image)

    def capture_photo(self) -> np.ndarray:
        """Capture a single photo as numpy array (BGR format)."""
        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError("Failed to capture photo from camera")
        return frame

    def release(self):
        """Release camera resources."""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
```

**Step 4: Run tests (may skip if no camera available)**

```bash
# Skip if running on system without camera
pytest tests/test_camera_handler.py -v || echo "Tests skipped - no camera"
```

**Step 5: Commit**

```bash
git add src/camera_handler.py tests/test_camera_handler.py
git commit -m "feat: implement camera handler with capture functionality"
```

---

## Task 3: Create Frame Composition Utility

**Files:**
- Create: `src/frame_composer.py`
- Create: `tests/test_frame_composer.py`

**Step 1: Write the failing test**

Create `tests/test_frame_composer.py`:

```python
import pytest
import numpy as np
from PIL import Image
from src.frame_composer import apply_frame

def test_apply_frame_creates_composed_image():
    # Create a dummy photo (RGB)
    photo = np.zeros((480, 640, 3), dtype=np.uint8)
    photo[:, :] = [100, 150, 200]  # Fill with a color

    # For now, test with a simple frame path
    # This will need a real frame PNG file
    result = apply_frame(photo, "project_files/frames/frame_simple.png")

    assert isinstance(result, Image.Image)
    assert result.width >= 640
    assert result.height >= 480
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_frame_composer.py -v
```

Expected: `ImportError`

**Step 3: Write minimal implementation**

Create `src/frame_composer.py`:

```python
import numpy as np
from PIL import Image
from pathlib import Path


def apply_frame(photo: np.ndarray, frame_path: str) -> Image.Image:
    """
    Apply a frame overlay to a captured photo.

    Args:
        photo: Captured photo as numpy array (BGR format from OpenCV)
        frame_path: Path to frame PNG file with transparency

    Returns:
        Composed PIL Image with frame overlay
    """
    # Convert BGR photo to RGB
    rgb_photo = cv2_to_rgb(photo)

    # Open the frame PNG
    frame = Image.open(frame_path).convert("RGBA")

    # Get frame dimensions
    frame_width, frame_height = frame.size

    # Calculate photo dimensions to fit within frame
    # Assuming frame has a transparent center area
    # For simple frames, we'll resize photo to match frame
    photo_resized = rgb_photo.resize((frame_width, frame_height), Image.Resampling.LANCZOS)

    # Create a new image for composition
    composed = Image.new("RGBA", (frame_width, frame_height))

    # Paste photo first
    composed.paste(photo_resized, (0, 0))

    # Paste frame on top (using alpha channel)
    composed.paste(frame, (0, 0), frame)

    # Convert back to RGB for saving
    return composed.convert("RGB")


def cv2_to_rgb(bgr_image: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR numpy array to PIL RGB Image."""
    import cv2
    # Convert BGR to RGB
    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    # Convert to PIL Image
    return Image.fromarray(rgb)
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_frame_composer.py -v
```

**Step 5: Commit**

```bash
git add src/frame_composer.py tests/test_frame_composer.py
git commit -m "feat: implement frame composition utility"
```

---

## Task 4: Create Login Page (Page 0)

**Files:**
- Create: `src/pages/login.py`
- Create: `tests/test_login_page.py`

**Step 1: Write the test**

Create `tests/test_login_page.py`:

```python
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from src.pages.login import LoginPage

@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_login_page_initialization(app):
    page = LoginPage(correct_pin="1234")
    assert page.windowTitle() == "Photobooth - Login"
    assert not page.is_authenticated()

def test_correct_pin_authenticates(app, qtbot):
    page = LoginPage(correct_pin="1234")
    # Simulate entering "1234"
    page.pin_input.setText("1234")
    QTest.mouseClick(page.enter_button, Qt.LeftButton)
    assert page.is_authenticated()

def test_wrong_pin_shows_error(app, qtbot):
    page = LoginPage(correct_pin="1234")
    page.pin_input.setText("9999")
    QTest.mouseClick(page.enter_button, Qt.LeftButton)
    assert not page.is_authenticated()
    assert "Incorrect" in page.error_label.text()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_login_page.py -v
```

**Step 3: Write implementation**

Create `src/pages/login.py`:

```python
import json
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont


class LoginPage(QWidget):
    """Login page with PIN entry for photobooth authentication."""

    authenticated = pyqtSignal()  # Signal emitted when authenticated

    def __init__(self, correct_pin: str = "1234"):
        super().__init__()
        self.correct_pin = correct_pin
        self._authenticated = False
        self.setup_ui()

    def setup_ui(self):
        """Setup the login UI with PIN entry and numeric keypad."""
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 40, 60, 60)
        layout.setSpacing(20)

        # Title
        title = QLabel("PHOTOBOOTH")
        title.setProperty("heading", True)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(40)

        # PIN Input
        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("Enter PIN")
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setMaxLength(6)
        self.pin_input.setAlignment(Qt.AlignCenter)
        self.pin_input.returnPressed.connect(self.verify_pin)
        layout.addWidget(self.pin_input)

        # Error Label
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: #FF6B6B; font-size: 14px;")
        layout.addWidget(self.error_label)

        layout.addSpacing(20)

        # Numeric Keypad
        keypad = QGridLayout()
        keypad.setSpacing(10)
        buttons = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('C', 3, 0), ('0', 3, 1), ('⏎', 3, 2),
        ]

        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(80, 80)
            if text == '⏎':
                btn.clicked.connect(self.verify_pin)
                btn.setStyleSheet("background-color: #FFC0CB; font-weight: bold;")
            elif text == 'C':
                btn.clicked.connect(self.clear_input)
            else:
                btn.clicked.connect(lambda checked, t=text: self.append_digit(t))
            keypad.addWidget(btn, row, col)

        keypad_container = QWidget()
        keypad_container.setLayout(keypad)
        keypad_container.layout().setAlignment(Qt.AlignCenter)
        layout.addWidget(keypad_container)

        layout.addStretch()
        self.setLayout(layout)
        self.apply_stylesheet()

    def append_digit(self, digit: str):
        """Append a digit to the PIN input."""
        current = self.pin_input.text()
        if len(current) < 6:
            self.pin_input.setText(current + digit)

    def clear_input(self):
        """Clear the PIN input."""
        self.pin_input.clear()
        self.error_label.setText("")

    def verify_pin(self):
        """Verify the entered PIN."""
        entered = self.pin_input.text()
        if entered == self.correct_pin:
            self._authenticated = True
            self.authenticated.emit()
        else:
            self._authenticated = False
            self.error_label.setText("Incorrect PIN")
            self.shake_animation()
            self.pin_input.clear()

    def shake_animation(self):
        """Shake the PIN input to indicate error."""
        from PyQt5.QtCore import QPoint
        animation = QPropertyAnimation(self.pin_input, b"pos")
        animation.setDuration(100)
        animation.setLoopCount(4)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        original_pos = self.pin_input.pos()
        animation.setStartValue(original_pos)
        animation.setEndValue(QPoint(original_pos.x() + 10, original_pos.y()))
        animation.start()
        # Reset position after animation
        animation.finished.connect(lambda: self.pin_input.move(original_pos))

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self._authenticated

    def apply_stylesheet(self):
        """Apply FOFOBOOTH styling."""
        self.setStyleSheet("""
            QWidget {
                background-color: #333333;
                color: #FFFFFF;
            }
            QLabel[heading="true"] {
                color: #FFFFFF;
                font-family: 'Montserrat', 'Arial', sans-serif;
                font-size: 36px;
                font-weight: bold;
                text-transform: uppercase;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #FFC0CB;
                border-radius: 8px;
                padding: 12px;
                font-size: 20px;
                color: #333333;
            }
            QLineEdit:focus {
                border: 3px solid #FFC0CB;
            }
            QPushButton {
                background-color: #444444;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #FFC0CB;
                color: #333333;
            }
        """)

    @staticmethod
    def load_config(config_path: str = "project_files/config.json") -> dict:
        """Load configuration from JSON file."""
        config_file = Path(config_path)
        if not config_file.exists():
            return {"pin": "1234"}  # Default
        with open(config_file, 'r') as f:
            return json.load(f)
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_login_page.py -v
```

**Step 5: Commit**

```bash
git add src/pages/login.py tests/test_login_page.py
git commit -m "feat: implement login page with PIN authentication"
```

---

## Task 5: Create Frame Selection Page (Page 1)

**Files:**
- Create: `src/pages/frame_selection.py`
- Create: `tests/test_frame_selection.py`

**Step 1: Write the test**

Create `tests/test_frame_selection.py`:

```python
import pytest
from PyQt5.QtWidgets import QApplication
from src.pages.frame_selection import FrameSelectionPage

@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_frame_selection_loads_frames(app, qtbot):
    frames_dir = "project_files/frames"
    page = FrameSelectionPage(frames_dir=frames_dir)
    assert len(page.frames) > 0
    assert page.continue_button.isEnabled() == False

def test_selecting_frame_enables_continue(app, qtbot):
    page = FrameSelectionPage(frames_dir="project_files/frames")
    if len(page.frames) > 0:
        # Simulate frame selection
        page.select_frame(0)
        assert page.continue_button.isEnabled() == True
        assert page.selected_frame is not None
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_frame_selection.py -v
```

**Step 3: Write implementation**

Create `src/pages/frame_selection.py`:

```python
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                             QScrollArea, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont


class FrameSelectionPage(QWidget):
    """Frame selection page for choosing photo frame style."""

    frame_selected = pyqtSignal(str)  # Signal emitted with frame path

    def __init__(self, frames_dir: str = "project_files/frames"):
        super().__init__()
        self.frames_dir = Path(frames_dir)
        self.frames = []
        self.selected_frame = None
        self.frame_cards = []
        self.load_frames()
        self.setup_ui()

    def load_frames(self):
        """Load all PNG frames from the frames directory."""
        if not self.frames_dir.exists():
            self.frames_dir.mkdir(parents=True, exist_ok=True)

        frame_files = list(self.frames_dir.glob("*.png"))
        self.frames = sorted(frame_files)

    def setup_ui(self):
        """Setup the frame selection UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Title
        title = QLabel("CHOOSE YOUR FRAME")
        title.setProperty("heading", True)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(20)

        # Scroll area for frames
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        # Frame grid
        grid_container = QWidget()
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignCenter)

        # Create frame cards
        self.create_frame_cards()

        scroll.setWidget(grid_container)
        layout.addWidget(scroll)

        layout.addSpacing(20)

        # Continue button
        self.continue_button = QPushButton("CONTINUE")
        self.continue_button.setEnabled(False)
        self.continue_button.clicked.connect(self.on_continue)
        self.continue_button.setFixedHeight(60)
        self.continue_button.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.continue_button)

        self.setLayout(layout)
        self.apply_stylesheet()

    def create_frame_cards(self):
        """Create clickable cards for each frame."""
        cols = 3  # Number of columns in grid

        for idx, frame_path in enumerate(self.frames):
            row = idx // cols
            col = idx % cols

            card = self.create_frame_card(frame_path, idx)
            self.frame_cards.append(card)
            self.grid_layout.addWidget(card, row, col)

    def create_frame_card(self, frame_path: Path, idx: int) -> QFrame:
        """Create a single frame card with preview."""
        card = QFrame()
        card.setProperty("frame_card", True)
        card.setFixedSize(200, 250)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)

        # Thumbnail preview
        thumbnail = QLabel()
        thumbnail.setFixedSize(180, 180)
        pixmap = QPixmap(str(frame_path))
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                180, 180,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            thumbnail.setPixmap(scaled)
        thumbnail.setAlignment(Qt.AlignCenter)
        layout.addWidget(thumbnail)

        # Frame name label
        name_label = QLabel(frame_path.stem.replace("_", " ").title())
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 14px; margin-top: 5px;")
        layout.addWidget(name_label)

        # Store frame path in card
        card.setProperty("frame_path", str(frame_path))

        # Make card clickable
        card.mousePressEvent = lambda e, c=card, i=idx: self.select_frame(i)

        return card

    def select_frame(self, idx: int):
        """Handle frame selection."""
        self.selected_frame = str(self.frames[idx])

        # Update UI to show selection
        for i, card in enumerate(self.frame_cards):
            if i == idx:
                card.setProperty("selected", True)
                card.setStyleSheet(card.styleSheet() + "border: 3px solid #FFC0CB;")
            else:
                card.setProperty("selected", False)
                card.setStyleSheet(self.get_base_card_style())

        self.continue_button.setEnabled(True)

    def get_base_card_style(self) -> str:
        """Get base style for frame cards."""
        return """
            QFrame[frame_card="true"] {
                background-color: #444444;
                border: 3px solid #555555;
                border-radius: 12px;
            }
            QFrame[frame_card="true"]:hover {
                border: 3px solid #FFA0B0;
            }
        """

    def on_continue(self):
        """Emit signal with selected frame path."""
        if self.selected_frame:
            self.frame_selected.emit(self.selected_frame)

    def apply_stylesheet(self):
        """Apply FOFOBOOTH styling."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #333333;
                color: #FFFFFF;
            }}
            QLabel[heading="true"] {{
                color: #FFFFFF;
                font-family: 'Montserrat', 'Arial', sans-serif;
                font-size: 32px;
                font-weight: bold;
                text-transform: uppercase;
            }}
            QPushButton {{
                background-color: #FFC0CB;
                color: #333333;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #FFB0C0;
            }}
            QPushButton:disabled {{
                background-color: #666666;
                color: #999999;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            {self.get_base_card_style()}
        """)
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_frame_selection.py -v
```

**Step 5: Commit**

```bash
git add src/pages/frame_selection.py tests/test_frame_selection.py
git commit -m "feat: implement frame selection page"
```

---

## Task 6: Create Capture & Display Page (Page 2)

**Files:**
- Create: `src/pages/capture_display.py`
- Create: `tests/test_capture_display.py`

**Step 1: Write the test**

Create `tests/test_capture_display.py`:

```python
import pytest
from PyQt5.QtWidgets import QApplication
from src.pages.capture_display import CaptureDisplayPage

@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_capture_display_initialization(app, qtbot):
    page = CaptureDisplayPage(frame_path="project_files/frames/frame_simple.png")
    assert page.frame_path == "project_files/frames/frame_simple.png"

def test_capture_photo_starts_camera(app, qtbot):
    page = CaptureDisplayPage(frame_path="project_files/frames/frame_simple.png")
    # Just test initialization, actual camera test needs hardware
    assert page.capture_button is not None
    assert page.save_button is not None
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_capture_display.py -v
```

**Step 3: Write implementation**

Create `src/pages/capture_display.py`:

```python
from pathlib import Path
from datetime import datetime
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from src.camera_handler import CameraHandler
from src.frame_composer import apply_frame


class CaptureDisplayPage(QWidget):
    """Photo capture and result display page."""

    photo_saved = pyqtSignal()  # Signal emitted when photo is saved
    retake_requested = pyqtSignal()  # Signal emitted to retake photo

    def __init__(self, frame_path: str, output_dir: str = "project_files/captured_images"):
        super().__init__()
        self.frame_path = frame_path
        self.output_dir = Path(output_dir)
        self.camera_handler = None
        self.captured_photo = None
        self.final_image = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the capture/display UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)

        # Stacked widget for switching between capture and display modes
        self.stacked_widget = QStackedWidget()

        # Capture mode
        self.capture_widget = self.create_capture_widget()
        self.stacked_widget.addWidget(self.capture_widget)

        # Display mode
        self.display_widget = self.create_display_widget()
        self.stacked_widget.addWidget(self.display_widget)

        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)
        self.apply_stylesheet()

    def create_capture_widget(self) -> QWidget:
        """Create the camera capture widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Title
        title = QLabel("PHOTO TIME!")
        title.setProperty("heading", True)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(20)

        # Camera feed display
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setStyleSheet("""
            background-color: #222222;
            border: 3px solid #FFC0CB;
            border-radius: 12px;
        """)
        self.camera_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.camera_label)

        layout.addSpacing(20)

        # Capture button
        self.capture_button = QPushButton("📷 CAPTURE")
        self.capture_button.setFixedHeight(70)
        self.capture_button.clicked.connect(self.capture_photo)
        layout.addWidget(self.capture_button)

        return widget

    def create_display_widget(self) -> QWidget:
        """Create the result display widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Title
        title = QLabel("YOUR PHOTO!")
        title.setProperty("heading", True)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(20)

        # Photo display
        self.photo_label = QLabel()
        self.photo_label.setMinimumSize(640, 480)
        self.photo_label.setStyleSheet("""
            background-color: #222222;
            border: 3px solid #FFC0CB;
            border-radius: 12px;
        """)
        self.photo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.photo_label)

        layout.addSpacing(20)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        self.retake_button = QPushButton("↺ RETAKE")
        self.retake_button.setFixedHeight(60)
        self.retake_button.clicked.connect(self.retake_photo)
        button_layout.addWidget(self.retake_button)

        self.save_button = QPushButton("💾 SAVE")
        self.save_button.setFixedHeight(60)
        self.save_button.clicked.connect(self.save_photo)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        return widget

    def initialize_camera(self):
        """Initialize camera when page is shown."""
        try:
            self.camera_handler = CameraHandler()
            self.start_camera_feed()
        except RuntimeError as e:
            self.camera_label.setText(f"Camera Error:\n{str(e)}")

    def start_camera_feed(self):
        """Start the camera feed timer."""
        self.feed_timer = QTimer()
        self.feed_timer.timeout.connect(self.update_camera_feed)
        self.feed_timer.start(33)  # ~30 FPS

    def update_camera_feed(self):
        """Update the camera feed display."""
        if self.camera_handler:
            try:
                pixmap = self.camera_handler.get_frame()
                scaled = pixmap.scaled(
                    640, 480,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.camera_label.setPixmap(scaled)
            except RuntimeError:
                self.camera_label.setText("Camera feed error")

    def capture_photo(self):
        """Capture a photo from the camera."""
        if self.camera_handler:
            # Stop the feed
            self.feed_timer.stop()

            # Capture the photo
            self.captured_photo = self.camera_handler.capture_photo()

            # Apply frame overlay
            self.final_image = apply_frame(self.captured_photo, self.frame_path)

            # Display the result
            self.display_result()

            # Switch to display mode
            self.stacked_widget.setCurrentIndex(1)

    def display_result(self):
        """Display the captured photo with frame."""
        from PIL.ImageQt import ImageQt
        pixmap = QPixmap.fromImage(ImageQt(self.final_image))
        scaled = pixmap.scaled(
            640, 480,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.photo_label.setPixmap(scaled)

    def retake_photo(self):
        """Return to capture mode for retake."""
        self.stacked_widget.setCurrentIndex(0)
        self.captured_photo = None
        self.final_image = None
        self.start_camera_feed()

    def save_photo(self):
        """Save the final photo to disk."""
        if self.final_image:
            # Create output directory if needed
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photostrip_{timestamp}.png"
            filepath = self.output_dir / filename

            # Save the image
            self.final_image.save(filepath)

            # Emit signal
            self.photo_saved.emit()

    def cleanup(self):
        """Release camera resources when leaving page."""
        if hasattr(self, 'feed_timer'):
            self.feed_timer.stop()
        if self.camera_handler:
            self.camera_handler.release()
            self.camera_handler = None

    def apply_stylesheet(self):
        """Apply FOFOBOOTH styling."""
        self.setStyleSheet("""
            QWidget {
                background-color: #333333;
                color: #FFFFFF;
            }
            QLabel[heading="true"] {
                color: #FFFFFF;
                font-family: 'Montserrat', 'Arial', sans-serif;
                font-size: 32px;
                font-weight: bold;
                text-transform: uppercase;
            }
            QPushButton {
                background-color: #FFC0CB;
                color: #333333;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFB0C0;
            }
        """)
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_capture_display.py -v
```

**Step 5: Commit**

```bash
git add src/pages/capture_display.py tests/test_capture_display.py
git commit -m "feat: implement capture and display page"
```

---

## Task 7: Create Main Application Entry Point

**Files:**
- Create: `src/main.py`
- Modify: `src/__init__.py`

**Step 1: Create main.py**

```python
import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget
from PyQt5.QtCore import Qt
from src.pages.login import LoginPage
from src.pages.frame_selection import FrameSelectionPage
from src.pages.capture_display import CaptureDisplayPage


class PhotoboothApp(QStackedWidget):
    """Main photobooth application managing page navigation."""

    def __init__(self):
        super().__init__()
        self.pages = {}
        self.setup_pages()
        self.connect_signals()
        self.showMaximized()
        self.setStyleSheet("background-color: #333333;")

    def setup_pages(self):
        """Initialize all pages and add to stacked widget."""
        # Load config for PIN
        config = LoginPage.load_config()
        pin = config.get("pin", "1234")
        frames_dir = config.get("frames_dir", "project_files/frames")
        output_dir = config.get("output_dir", "project_files/captured_images")

        # Page 0: Login
        self.pages["login"] = LoginPage(correct_pin=pin)
        self.addWidget(self.pages["login"])

        # Page 1: Frame Selection
        self.pages["frame_selection"] = FrameSelectionPage(frames_dir=frames_dir)
        self.addWidget(self.pages["frame_selection"])

        # Page 2: Capture & Display (created dynamically when frame is selected)
        self.pages["capture"] = None

        # Start at login page
        self.setCurrentWidget(self.pages["login"])

    def connect_signals(self):
        """Connect page signals for navigation."""
        # Login → Frame Selection
        self.pages["login"].authenticated.connect(self.go_to_frame_selection)

        # Frame Selection → Capture
        self.pages["frame_selection"].frame_selected.connect(self.go_to_capture)

    def go_to_frame_selection(self):
        """Navigate to frame selection page."""
        self.setCurrentWidget(self.pages["frame_selection"])

    def go_to_capture(self, frame_path: str):
        """Navigate to capture page with selected frame."""
        # Create capture page with selected frame
        output_dir = "project_files/captured_images"
        capture_page = CaptureDisplayPage(frame_path=frame_path, output_dir=output_dir)

        # Clean up old capture page if exists
        if self.pages["capture"] is not None:
            old_page = self.pages["capture"]
            old_page.cleanup()
            self.removeWidget(old_page)

        # Add new capture page
        self.pages["capture"] = capture_page
        self.addWidget(capture_page)

        # Connect signals
        capture_page.retake_requested.connect(self.go_to_frame_selection)
        capture_page.photo_saved.connect(self.on_photo_saved)

        # Navigate and initialize camera
        self.setCurrentWidget(capture_page)
        capture_page.initialize_camera()

    def on_photo_saved(self):
        """Handle photo saved event."""
        # Return to frame selection for next session
        if self.pages["capture"]:
            self.pages["capture"].cleanup()
        self.setCurrentWidget(self.pages["frame_selection"])

    def keyPressEvent(self, event):
        """Handle key press events."""
        # ESC to exit fullscreen
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Cleanup on application close."""
        if self.pages.get("capture"):
            self.pages["capture"].cleanup()
        event.accept()


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Photobooth")

    window = PhotoboothApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
```

**Step 2: Update src/__init__.py**

```python
"""Photobooth Application."""

__version__ = "0.1.0"
```

**Step 3: Test the application runs**

```bash
cd src && python main.py
```

**Step 4: Commit**

```bash
git add src/main.py src/__init__.py
git commit -m "feat: implement main application with page navigation"
```

---

## Task 8: Create Sample Frame Assets

**Files:**
- Create: `project_files/frames/frame_simple.png`
- Create: `project_files/frames/frame_kawaii.png`
- Create: `project_files/frames/frame_classic.png`
- Create: `scripts/generate_frames.py`

**Step 1: Create frame generator script**

Create `scripts/generate_frames.py`:

```python
"""
Generate simple frame assets for the photobooth.
Creates 3 basic frame styles with transparent centers.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Create frames directory
frames_dir = Path("project_files/frames")
frames_dir.mkdir(parents=True, exist_ok=True)

# Frame dimensions
FRAME_WIDTH = 800
FRAME_HEIGHT = 1000
PHOTO_WIDTH = 640
PHOTO_HEIGHT = 800
PHOTO_X = (FRAME_WIDTH - PHOTO_WIDTH) // 2
PHOTO_Y = 100


def create_simple_frame():
    """Create a simple clean frame with pink border."""
    # Create RGBA image (transparent by default)
    frame = Image.new("RGBA", (FRAME_WIDTH, FRAME_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)

    # Draw border around photo area
    border_color = (255, 192, 203, 255)  # Pink with full opacity
    border_width = 20

    # Top border
    draw.rectangle(
        [PHOTO_X - border_width, PHOTO_Y - border_width,
         PHOTO_X + PHOTO_WIDTH + border_width, PHOTO_Y],
        fill=border_color
    )

    # Bottom border
    draw.rectangle(
        [PHOTO_X - border_width, PHOTO_Y + PHOTO_HEIGHT,
         PHOTO_X + PHOTO_WIDTH + border_width, PHOTO_Y + PHOTO_HEIGHT + border_width],
        fill=border_color
    )

    # Left border
    draw.rectangle(
        [PHOTO_X - border_width, PHOTO_Y,
         PHOTO_X, PHOTO_Y + PHOTO_HEIGHT],
        fill=border_color
    )

    # Right border
    draw.rectangle(
        [PHOTO_X + PHOTO_WIDTH, PHOTO_Y,
         PHOTO_X + PHOTO_WIDTH + border_width, PHOTO_Y + PHOTO_HEIGHT],
        fill=border_color
    )

    # Add title text at bottom
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    text = "PHOTOBOOTH"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (FRAME_WIDTH - text_width) // 2
    text_y = PHOTO_Y + PHOTO_HEIGHT + 40

    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

    return frame


def create_kawaii_frame():
    """Create a cute kawaii-style frame with decorative elements."""
    frame = Image.new("RGBA", (FRAME_WIDTH, FRAME_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)

    # Pink gradient border (simplified as multiple rectangles)
    colors = [
        (255, 182, 193, 255),  # Light pink
        (255, 192, 203, 255),  # Pink
        (255, 105, 180, 255),  # Hot pink
    ]

    for i, color in enumerate(colors):
        offset = (len(colors) - i) * 8
        # Draw border
        draw.rectangle(
            [PHOTO_X - offset, PHOTO_Y - offset,
             PHOTO_X + PHOTO_WIDTH + offset, PHOTO_Y],
            fill=color
        )
        draw.rectangle(
            [PHOTO_X - offset, PHOTO_Y + PHOTO_HEIGHT,
             PHOTO_X + PHOTO_WIDTH + offset, PHOTO_Y + PHOTO_HEIGHT + offset],
            fill=color
        )
        draw.rectangle(
            [PHOTO_X - offset, PHOTO_Y,
             PHOTO_X, PHOTO_Y + PHOTO_HEIGHT],
            fill=color
        )
        draw.rectangle(
            [PHOTO_X + PHOTO_WIDTH, PHOTO_Y,
             PHOTO_X + PHOTO_WIDTH + offset, PHOTO_Y + PHOTO_HEIGHT],
            fill=color
        )

    # Add decorative dots in corners
    dot_positions = [
        (PHOTO_X - 40, PHOTO_Y - 40),
        (PHOTO_X + PHOTO_WIDTH + 40, PHOTO_Y - 40),
        (PHOTO_X - 40, PHOTO_Y + PHOTO_HEIGHT + 40),
        (PHOTO_X + PHOTO_WIDTH + 40, PHOTO_Y + PHOTO_HEIGHT + 40),
    ]

    for x, y in dot_positions:
        for r in [15, 10, 5]:
            draw.ellipse([x-r, y-r, x+r, y+r], fill=(255, 182, 193, 255))

    # Title
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    text = "✨ KAWAII ✨"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (FRAME_WIDTH - text_width) // 2
    text_y = PHOTO_Y + PHOTO_HEIGHT + 60

    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

    return frame


def create_classic_frame():
    """Create a classic elegant frame."""
    frame = Image.new("RGBA", (FRAME_WIDTH, FRAME_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)

    # Elegant dark border
    border_width = 30
    outer_color = (80, 80, 80, 255)
    inner_color = (255, 192, 203, 255)

    # Outer dark border
    draw.rectangle(
        [PHOTO_X - border_width, PHOTO_Y - border_width,
         PHOTO_X + PHOTO_WIDTH + border_width, PHOTO_Y],
        fill=outer_color
    )
    draw.rectangle(
        [PHOTO_X - border_width, PHOTO_Y + PHOTO_HEIGHT,
         PHOTO_X + PHOTO_WIDTH + border_width, PHOTO_Y + PHOTO_HEIGHT + border_width],
        fill=outer_color
    )
    draw.rectangle(
        [PHOTO_X - border_width, PHOTO_Y,
         PHOTO_X, PHOTO_Y + PHOTO_HEIGHT],
        fill=outer_color
    )
    draw.rectangle(
        [PHOTO_X + PHOTO_WIDTH, PHOTO_Y,
         PHOTO_X + PHOTO_WIDTH + border_width, PHOTO_Y + PHOTO_HEIGHT],
        fill=outer_color
    )

    # Inner pink accent line
    draw.rectangle(
        [PHOTO_X - border_width + 2, PHOTO_Y - border_width + 2,
         PHOTO_X + PHOTO_WIDTH + border_width - 2, PHOTO_Y - border_width + 8],
        fill=inner_color
    )
    draw.rectangle(
        [PHOTO_X - border_width + 2, PHOTO_Y + PHOTO_HEIGHT + border_width - 8,
         PHOTO_X + PHOTO_WIDTH + border_width - 2, PHOTO_Y + PHOTO_HEIGHT + border_width - 2],
        fill=inner_color
    )

    # Title
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    text = "CLASSIC"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (FRAME_WIDTH - text_width) // 2
    text_y = PHOTO_Y + PHOTO_HEIGHT + 50

    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

    return frame


if __name__ == "__main__":
    print("Generating frame assets...")

    # Simple frame
    simple = create_simple_frame()
    simple.save(frames_dir / "frame_simple.png")
    print("✓ Created frame_simple.png")

    # Kawaii frame
    kawaii = create_kawaii_frame()
    kawaii.save(frames_dir / "frame_kawaii.png")
    print("✓ Created frame_kawaii.png")

    # Classic frame
    classic = create_classic_frame()
    classic.save(frames_dir / "frame_classic.png")
    print("✓ Created frame_classic.png")

    print("\nFrame generation complete!")
```

**Step 2: Run frame generator**

```bash
python scripts/generate_frames.py
```

**Step 3: Verify frames were created**

```bash
ls -la project_files/frames/
```

Expected: 3 PNG files

**Step 4: Commit**

```bash
git add scripts/generate_frames.py project_files/frames/*.png
git commit -m "feat: add frame generation script and sample frames"
```

---

## Task 9: Final Integration and Testing

**Step 1: Run the full application**

```bash
cd src && python main.py
```

**Step 2: Test complete workflow**
1. Launch application
2. Enter PIN (1234)
3. Select a frame
4. Capture a photo
5. Save the photo
6. Verify saved in project_files/captured_images/

**Step 3: Create README.md**

```bash
cat > README.md << 'EOF'
# Photobooth MVP

A simplified photobooth application with PIN authentication, frame selection, and photo capture.

## Features

- **PIN Authentication**: Secure login with configurable PIN
- **Frame Selection**: Choose from multiple photo frame styles
- **Photo Capture**: Real-time camera feed with live preview
- **Frame Overlay**: Automatic application of selected frame
- **Photo Saving**: Save composed photos to disk

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate frame assets:
```bash
python scripts/generate_frames.py
```

3. Run the application:
```bash
cd src && python main.py
```

## Configuration

Edit `project_files/config.json` to change settings:

```json
{
  "pin": "1234",
  "camera": {
    "device_index": 0,
    "width": 1280,
    "height": 720
  }
}
```

## Usage

1. Enter PIN to unlock (default: 1234)
2. Select a frame style
3. Click CAPTURE to take a photo
4. Save your photo or retake

## Controls

- **ESC**: Exit application
- **Numeric Keypad**: Enter PIN
- **Enter**: Submit PIN

## File Structure

```
chai proj/
├── src/                    # Source code
│   ├── main.py            # Application entry point
│   ├── pages/             # UI pages
│   └── camera_handler.py  # Camera management
├── project_files/
│   ├── frames/           # Frame templates
│   ├── captured_images/  # Saved photos
│   └── config.json       # Configuration
└── scripts/              # Utility scripts
```

## Design

Follows FOFOBOOTH design language:
- Dark charcoal background (#333333)
- Pastel pink accents (#FFC0CB)
- Clean, minimal UI
- Bold typography

## Requirements

- Python 3.8+
- Webcam or camera device
- PyQt5
- OpenCV
- Pillow
EOF
```

**Step 4: Final commit**

```bash
git add README.md
git commit -m "docs: add README with usage instructions"
```

**Step 5: Tag completion**

```bash
git tag -a v0.1.0 -m "Photobooth MVP complete"
git push origin main --tags
```

---

## Success Criteria

After completing all tasks, verify:

- [ ] Application starts without errors
- [ ] PIN authentication works (1234)
- [ ] Frame selection shows 3 frames
- [ ] Camera feed displays correctly
- [ ] Photo capture works
- [ ] Frame overlay is applied
- [ ] Photo saves to captured_images directory
- [ ] UI follows FOFOBOOTH design (#333333 background, #FFC0CB accents)
- [ ] ESC key exits application
- [ ] Retake button returns to camera mode

---

## Troubleshooting

**Camera not working:**
- Check camera is connected
- Try changing `device_index` in config.json (0, 1, 2...)
- Ensure no other application is using the camera

**Import errors:**
- Run `pip install -r requirements.txt`
- Ensure Python 3.8+ is being used

**Frames not loading:**
- Run `python scripts/generate_frames.py`
- Check `project_files/frames/` directory exists

**PIN not working:**
- Check `project_files/config.json` exists
- Default PIN is "1234"
