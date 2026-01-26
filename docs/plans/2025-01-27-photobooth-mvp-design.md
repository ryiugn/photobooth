# Photobooth MVP Design Document

**Date:** 2025-01-27
**Version:** Simplified MVP

## Overview

A simplified photobooth application with PIN authentication, frame selection, and photo capture/display functionality. The design follows FOFOBOOTH aesthetics with dark charcoal backgrounds and pink accents.

## Scope

This MVP includes:
1. **Page 0**: Simple PIN entry screen for authentication
2. **Page 1**: Frame selection gallery (3 built-in frames)
3. **Page 2**: Camera capture with frame overlay and display

## Architecture

### Application Structure

Single PyQt5 application with `QStackedWidget` managing 3 pages:
- **Page 0 - Login**: PIN entry screen
- **Page 1 - Frame Selection**: Gallery of available frames
- **Page 2 - Capture & Display**: Camera feed → capture → show result

### Technology Stack

- **Python 3**: Primary language
- **PyQt5**: GUI framework with QStackedWidget for page navigation
- **OpenCV (cv2)**: Camera access and image capture
- **Pillow (PIL)**: Image composition and frame overlay
- **NumPy**: Image array manipulation

### Project Structure

```
chai proj/
├── src/
│   ├── main.py                 # Entry point with QStackedWidget
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── login.py            # PIN entry screen
│   │   ├── frame_selection.py  # Frame gallery
│   │   └── capture_display.py  # Camera & result display
│   └── camera_handler.py       # Camera management (simplified)
├── project_files/
│   ├── frames/                 # Frame templates (3 PNG files)
│   │   ├── frame_simple.png
│   │   ├── frame_kawaii.png
│   │   └── frame_classic.png
│   ├── captured_images/        # Saved photos
│   └── config.json             # PIN and basic settings
├── docs/
│   └── plans/
│       └── 2025-01-27-photobooth-mvp-design.md
└── requirements.txt
```

## Page Designs

### Page 0 - Login Screen

**Components:**
- Centered PIN entry interface on dark charcoal background (#333333)
- Application title "PHOTOBOOTH" in bold sans-serif, white text, top center
- PIN input field (4-6 digits, masked with ••••) with pink border
- Numeric keypad (0-9 + clear + enter) with rounded buttons
- Large "ENTER" button in pastel pink (#FFC0CB)
- Error message area below input (hidden by default)

**UI Elements:**
- `QLabel` for title and error messages
- `QLineEdit` with `setEchoMode(QLineEdit.Password)` for PIN
- `QGridLayout` for numeric keypad buttons
- Pink accent color for selected/hover states

**Behavior:**
- Verify PIN against config.json value
- Show error message on incorrect PIN
- Transition to Page 1 on successful authentication

### Page 1 - Frame Selection

**Components:**
- Title "CHOOSE YOUR FRAME" centered at top
- Grid layout showing 3 frame options
- Each frame option shows:
  - Thumbnail preview (QLabel with QPixmap)
  - Frame name label below
  - Rounded border, highlights in pink when selected
- "CONTINUE" button at bottom (enabled after selection)

**UI Elements:**
- `QGridLayout` for frame gallery
- Frame data loaded from `project_files/frames/` directory
- Selected frame stored in application state

**Behavior:**
- Load all PNG files from frames directory
- Highlight selected frame with pink border
- Enable "CONTINUE" button only after selection
- Transition to Page 2 with selected frame path

### Page 2 - Capture & Display

**Components:**
- Split view or toggle between:
  1. **Camera mode**: Live feed (QLabel with continuous cv2 updates) + "CAPTURE" button
  2. **Display mode**: Captured photo with frame overlay + "RETAKE" and "SAVE" buttons
- Pink accent borders around active elements

**UI Elements:**
- `QLabel` for camera feed and photo display
- `QPushButton` for capture/retake/save actions
- Timer for periodic camera feed updates (~30 FPS)

**Behavior:**
- Initialize camera on page entry
- Display live camera feed
- On capture: Stop feed, apply frame overlay, show result
- "RETAKE": Return to camera mode
- "SAVE": Save composed image to captured_images directory

## Data Flow & State Management

### Application State

```python
class AppState:
    authenticated: bool      # False until PIN is verified
    selected_frame: str      # Path to selected frame PNG
    captured_image: ndarray  # Photo from camera (before frame)
    final_image: Image       # Composed photo + frame
```

### Flow Sequence

1. **Login → Frame Selection**: Only allow transition after correct PIN
2. **Frame Selection → Capture**: Only allow transition after frame is selected
3. **Capture → Display**: After photo taken, compose with frame, show result
4. **Display → Frame Selection**: "Retake" returns to frame selection

### Camera Handler

```python
class CameraHandler:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)  # Default camera

    def get_frame(self) -> QPixmap:
        # Capture frame, convert BGR→RGB, return QPixmap

    def capture_photo(self) -> ndarray:
        # Return single frame as numpy array

    def release(self):
        # Clean up camera resources
```

### Frame Composition

```python
def apply_frame(photo: ndarray, frame_path: str) -> Image:
    # Open frame PNG (with transparency)
    # Resize photo to match frame inner dimensions
    # Paste photo behind frame overlay
    # Return composed PIL Image
```

## Styling & FOFOBOOTH Design Language

### Color Palette

- **Background**: #333333 (dark charcoal)
- **Accent**: #FFC0CB (pastel pink)
- **Text**: #FFFFFF (white)
- **Secondary**: #444444, #666666 (grays for disabled/hover states)

### QSS Stylesheet

```css
/* Main Application */
QStackedWidget, QWidget {
    background-color: #333333;
}

/* Title Text */
QLabel[heading="true"] {
    color: #FFFFFF;
    font-family: 'Montserrat', 'Poppins', sans-serif;
    font-size: 32px;
    font-weight: bold;
    text-transform: uppercase;
}

/* Buttons */
QPushButton {
    background-color: #FFC0CB;
    color: #333333;
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #FFB0C0;
}

QPushButton:disabled {
    background-color: #666666;
    color: #999999;
}

/* Input Fields */
QLineEdit {
    background-color: #FFFFFF;
    border: 2px solid #FFC0CB;
    border-radius: 8px;
    padding: 10px;
    font-size: 18px;
}

/* Frame Cards */
QFrame[frame_card="true"] {
    background-color: #444444;
    border: 3px solid #555555;
    border-radius: 12px;
    padding: 10px;
}

QFrame[frame_card="true"][selected="true"] {
    border: 3px solid #FFC0CB;
}
```

### Layout Principles

- Centered content with generous margins (40-60px from edges)
- Minimum 12px padding between elements
- Round corners (8-12px border-radius)
- High contrast: white text on dark backgrounds
- Pink highlights for interactive/selected states

## Error Handling

### Login Page
- **Wrong PIN**: Shake animation + "Incorrect PIN" message
- **Empty input**: "Please enter a PIN" message

### Frame Selection
- **Missing frame files**: Show placeholder or skip unavailable frames
- **No frames found**: Display "No frames available" message

### Camera Capture
- **Camera not available**: "Camera error - check connection" message
- **Camera already in use**: Attempt to release and reinitialize
- **Capture failure**: Retry button or return to frame selection

## Configuration

### config.json

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

### requirements.txt

```
PyQt5==5.15.9
opencv-python==4.8.0.74
Pillow==10.0.0
numpy==1.24.3
```

## Implementation Notes

- **Frame assets**: Need 3 PNG frame files with transparency (simple, kawaii, classic styles)
- **Camera device index**: 0 for default camera, may need adjustment
- **Frame composition**: Frames should have transparent center area for photo overlay
- **Photo saving**: Filename format `photostrip_YYYYMMDD_HHMMSS.png`

## Success Criteria

- [ ] User can enter PIN and authenticate
- [ ] User can select from 3 available frames
- [ ] Camera feed displays correctly
- [ ] Photo can be captured with frame overlay
- [ ] Final image can be saved to disk
- [ ] UI follows FOFOBOOTH design language
- [ ] Application handles camera errors gracefully
