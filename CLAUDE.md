# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Workflow

**CRITICAL**: The appropriate superpowers plugin MUST be used at ALL stages of development. Superpowers must be invoked before ANY work begins - including planning, implementation, debugging, testing, code review, and completion verification. No development task should be started without first invoking the relevant superpower skill.

Available superpowers skills:
- `superpowers:brainstorming` - MUST use before any creative work (features, components, functionality)
- `superpowers:systematic-debugging` - MUST use when encountering bugs, test failures, or unexpected behavior
- `superpowers:test-driven-development` - MUST use when implementing features or bugfixes (before writing implementation code)
- `superpowers:requesting-code-review` - MUST use after completing tasks or implementing major features
- `superpowers:writing-plans` - MUST use when you have requirements for multi-step tasks
- `superpowers:verification-before-completion` - MUST use before claiming work is complete, fixing, or passing

**DEPLOYMENT POLICY - CRITICAL**:
- **ALWAYS check for existing deployments BEFORE creating new ones**
- Use Vercel CLI to check current deployment URLs:
  ```bash
  # Check API backend deployments
  cd api
  vercel list --yes

  # Check web frontend deployments
  cd ../web
  vercel list --yes
  ```
- Reuse existing deployments when possible - only deploy new versions when code has changed
- Deployment URLs change with each deploy - update environment variables after deploying
- See README.md "Checking Deployment URLs (REQUIRED)" section for full details

## Project Overview

This is a photobooth project that implements a **4-page secure camera application** with real-time image capture, frame selection, and photostrip generation. The application follows a simple, user-friendly flow with authentication:

0. **Page 0 - Login Screen**: Secure authentication before accessing the application
1. **Page 1 - Frame Selection**: Choose from available photo frames
2. **Page 2 - Photo Capture**: Countdown timer and camera feed for taking photos
3. **Page 3 - Photostrip Reveal**: Display final photostrip with download, retake, and print options

## Design Language & Style

**CRITICAL**: The UI/UX design MUST draw inspiration from and closely resemble the aesthetic of [FOFOBOOTH](https://fofobooth.cc). All visual design decisions should align with this reference.

### Core Design Principles

- **Overall Aesthetic**: Contemporary and whimsical, blending clean lines with soft, friendly details. Fun yet polished vibe.
- **Color Scheme**: Deep charcoal gray (#333333) background, soft pastel pink (#FFC0CB) accents, white (#FFFFFF) text.
- **Typography**: Bold sans-serif (Montserrat/Poppins), all-caps branding, high contrast.
- **Layout**: Centered symmetrical layout, generous white space, single-column structure.
- **UI Elements**: Rounded buttons (8-12px radius), subtle shadows, pink butterfly motif for decorative accents.
- **Animations**: Subtle hover effects, smooth transitions between pages, gentle animations.
- **UX Principle**: **Keep it simple and easy to use** - minimal cognitive load, clear visual hierarchy, intuitive navigation.

### PyQt5 Implementation Guidelines

- Use QPalette for dark charcoal background (#333333)
- Apply rounded corners to buttons via stylesheet (border-radius: 8-12px)
- Use pastel pink (#FFC0CB) for accent colors and active/hover states
- Ensure ample padding and margins (12-16px minimum)
- Implement subtle drop shadows in QSS (box-shadow: 1-2px)
- Choose bold sans-serif fonts (Montserrat/Poppins) for branding
- Maintain generous spacing between UI elements
- Keep the interface clean and uncluttered

## Application Flow & Architecture

### Page 0: Login Screen

**Purpose**: Secure the application with authentication to prevent unauthorized access.

**Authentication Methods** (choose one or implement multiple):
- **PIN Code Entry**: Simple 4-6 digit PIN (recommended for kiosk mode)
- **Password Login**: Username and password combination
- **Admin Key Physical**: Physical button or key switch for hardware-based access
- **QR Code/Scanner**: Scan authorized QR code to unlock

**Components**:
- PIN/password input field with masked entry
- Numeric keypad for PIN entry (touch-friendly)
- "Enter" or "Unlock" button
- Error message display for failed attempts
- Attempt limit with lockout after N failed attempts (configurable)
- Application branding/logo

**Security Features**:
- Configurable PIN/password stored in `project_files/config.json` (hashed, not plaintext)
- Failed attempt logging to `project_files/logs/auth.log`
- Temporary lockout after multiple failed attempts (e.g., 5 attempts = 30 second lockout)
- Session timeout: Return to login after N minutes of inactivity (optional)
- Escape key or "Exit" button to close application completely

**State Management**:
- Authentication status flag (authenticated/not authenticated)
- Failed attempt counter
- Lockout timestamp (if locked out)
- Session start timestamp (for timeout tracking)

**Behavior**:
- First screen displayed on application launch
- Blocks all navigation until successful authentication
- Clear input field after failed attempt
- Show shake animation or visual feedback on failed attempt
- Log all authentication attempts (success and failure)

### Page 1: Frame Selection Screen

**Purpose**: Allow customers to choose a photo frame/style before capturing.

**Components**:
- Frame preview gallery (grid layout)
- Frame selection buttons with thumbnail previews
- "Start Photo Session" button to proceed to next page
- Visual feedback for selected frame

**State Management**:
- Store selected frame ID/name for use in photo capture
- Load frame templates from `project_files/frames/` directory

### Page 2: Photo Capture Screen

**Purpose**: Guide customers through the photo taking process with countdown and live preview.

**Components**:
- Live camera feed display (QLabel with continuous updates)
- Large countdown timer overlay (3-2-1 countdown before capture)
- Camera feed initialization using `cv2.VideoCapture`
- Capture button (or auto-capture after countdown)
- Progress indicator for multi-shot photostrips (e.g., "Photo 1 of 4")

**Behavior**:
- Initialize camera on page entry
- Display countdown animation (3 seconds) before each capture
- Capture multiple photos for photostrip (typically 4 photos)
- Convert frames from BGR to RGB for display
- Store captured images temporarily in memory

### Page 3: Photostrip Reveal Screen

**Purpose**: Display the final photostrip and provide action options.

**Components**:
- Photostrip preview display (composite of captured photos with selected frame)
- **Download** button: Save photostrip to customer's device
- **Retake** button: Return to Page 2 (Photo Capture) for new photos
- **Print** button: Send photostrip to configured printer
- Application branding/footer

**Storage/Backend**:
- Save photostrips to `project_files/captured_images/` directory
- Filename format: `photostrip_YYYYMMDD_HHMMSS.png`
- Maintain session history for potential print queue
- Automatically create directories if they don't exist

## Technology Stack

- **Python 3**: Primary programming language
- **PyQt5**: GUI framework with QStackedWidget for page navigation
- **OpenCV (cv2)**: Image capture and processing
- **picamera**: Raspberry Pi camera interface (alternative to cv2)
- **numpy**: Image array manipulation and composite generation
- **os/pathlib**: File system operations
- **PIL/Pillow**: Image composition and text overlay (for frames)
- **hashlib/bcrypt**: Password hashing for authentication (bcrypt recommended)
- **json**: Configuration and credentials storage
- **logging**: Authentication attempt logging

## Hardware Requirements

- Raspberry Pi with camera module OR USB webcam
- Compatible display/monitor (touchscreen recommended for kiosk mode)
- Camera cable properly connected
- Optional: Thermal printer for on-site printing

## File Structure

```
chai proj/
├── project_files/
│   ├── captured_images/       # Stored photostrips (backend storage)
│   ├── frames/                # Photo frame templates/assets
│   │   ├── frame_simple.png
│   │   ├── frame_kawaii.png
│   │   └── frame_classic.png
│   ├── logs/                  # Application and authentication logs
│   │   └── auth.log           # Authentication attempt logs
│   └── config.json            # App configuration (printer settings, credentials, etc.)
├── src/
│   ├── main.py                # Application entry point
│   ├── pages/
│   │   ├── login.py           # Page 0 - Login screen
│   │   ├── frame_selection.py # Page 1
│   │   ├── photo_capture.py   # Page 2
│   │   └── photostrip_reveal.py # Page 3
│   ├── auth_handler.py        # Authentication logic and session management
│   ├── camera_handler.py      # Camera management
│   ├── frame_manager.py       # Frame loading and application
│   └── storage_manager.py     # Backend storage operations
└── assets/
    ├── fonts/                 # Custom fonts (Montserrat, Poppins)
    └── icons/                 # UI icons and branding
```

## Configuration File (config.json)

```json
{
  "app_name": "Photobooth",
  "authentication": {
    "method": "pin",
    "pin_hash": "hashed_pin_here",
    "max_attempts": 5,
    "lockout_duration_seconds": 30,
    "session_timeout_minutes": 15
  },
  "camera": {
    "device_index": 0,
    "resolution": [1280, 720]
  },
  "photostrip": {
    "photos_per_strip": 4,
    "countdown_seconds": 3
  },
  "printer": {
    "enabled": true,
    "device": "/dev/usb/lp0"
  }
}
```

## Development Commands

### Running the Application
```bash
python src/main.py
```

### Installing Dependencies
```bash
pip install PyQt5 opencv-python picamera numpy Pillow bcrypt
```

## Key Implementation Details

1. **Page Navigation**: Use `QStackedWidget` to manage transitions between the 4 pages
2. **Authentication Flow**: Login screen (Page 0) must be successfully passed before any other page is accessible
3. **Camera Management**: Initialize camera once on Page 2 entry, release on exit
4. **State Management**: Pass selected frame and captured images between pages
5. **Photostrip Generation**: Composite 4 captured photos vertically with frame overlay
6. **Storage**: All photostrips saved to backend with unique timestamps
7. **Cleanup**: Properly release camera resources and close application on exit

## Security Considerations

**CRITICAL**: The application must prevent unauthorized access.

1. **Password Storage**:
   - NEVER store passwords in plaintext
   - Use bcrypt or similar hashing algorithm for PIN/password storage
   - Store only the hash in `config.json`

2. **Failed Attempt Handling**:
   - Log all failed authentication attempts with timestamp
   - Implement lockout after N consecutive failed attempts
   - Display generic error messages (don't reveal if PIN is partially correct)

3. **Session Management**:
   - Implement session timeout to return to login after inactivity
   - Clear sensitive data from memory when returning to login
   - Track authentication state throughout application lifecycle

4. **Configuration Security**:
   - Set appropriate file permissions on `config.json` (read/write for owner only)
   - Consider environment variables for sensitive credentials in production
   - Never commit credentials to version control

5. **Physical Security** (for kiosk deployment):
   - Run in fullscreen/kiosk mode to prevent OS access
   - Disable keyboard shortcuts for system exit
   - Consider physical enclosure to limit access to ports/buttons

## Common Issues

- **Camera not detected**: Ensure camera is properly connected and permissions are set
- **Permission errors**: Check write permissions for `project_files/captured_images/` and `project_files/logs/`
- **Display issues**: Verify PyQt5 installation and display configuration
- **Frame loading errors**: Ensure frame assets exist in `project_files/frames/`
- **Authentication failures**: Verify PIN hash in `config.json` is correctly generated using bcrypt
- **Lockout issues**: Check lockout duration setting in config and wait for lockout to expire
- **Config file errors**: Ensure `config.json` is valid JSON and contains all required fields
