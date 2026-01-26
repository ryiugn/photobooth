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
