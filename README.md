# Photobooth Application

A photobooth application with PIN authentication, per-photo frame selection, and photostrip generation. Available as both a **PyQt5 Desktop App** and a **Web Application**.

## Applications

### 1. Desktop Application (PyQt5)

A native desktop photobooth application for kiosk-style deployment.

**Features:**
- PIN Authentication
- 4-slot frame selection (different frame per photo)
- Template save/load functionality
- Real-time camera feed with countdown
- Photostrip generation with download/print

**Quick Start:**
```bash
pip install -r requirements.txt
cd src && python main.py
```

**Default PIN:** `1234`

### 2. Web Application (React + FastAPI)

A modern web-based photobooth accessible from any device with a browser.

**Features:**
- Same features as desktop app
- Browser-based camera access (WebRTC)
- Responsive design for mobile/desktop
- Deploy to Vercel (free tier)

**Quick Start:**
```bash
# Backend (FastAPI)
cd api && pip install -r requirements.txt && python main.py

# Frontend (React)
cd web && npm install && npm run dev
```

---

## Project Structure

```
chai proj/
├── src/                      # Desktop App (PyQt5)
│   ├── main.py              # Desktop app entry point
│   ├── pages/               # UI pages
│   ├── widgets/             # Custom widgets
│   ├── camera_handler.py    # Camera management
│   ├── frame_composer.py    # Photostrip composition
│   └── template_storage.py  # Template CRUD
│
├── api/                      # Web Backend (FastAPI)
│   ├── main.py              # Vercel serverless entry
│   ├── routes/              # API endpoints
│   ├── config/              # Configuration
│   ├── requirements.txt     # Python deps
│   └── vercel.json          # Vercel config
│
├── web/                      # Web Frontend (React)
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── state/           # Zustand store
│   │   ├── services/        # API service
│   │   └── types/           # TypeScript types
│   ├── package.json
│   ├── vite.config.ts
│   └── vercel.json
│
├── project_files/
│   ├── frames/              # Frame templates
│   ├── templates/           # Saved templates
│   ├── captured_images/     # Desktop app output
│   ├── sessions/            # Web app temp storage
│   └── strips/              # Web app output
│
├── scripts/                  # Utility scripts
├── docs/
│   └── plans/               # Design documents
└── requirements.txt          # Desktop app deps
```

---

## Desktop Application

### Installation

```bash
pip install PyQt5 opencv-python Pillow numpy
```

### Configuration

Edit `project_files/config.json`:

```json
{
  "app_name": "Photobooth",
  "pin": "1234",
  "camera": {
    "device_index": 0,
    "width": 1280,
    "height": 720
  },
  "photostrip": {
    "photos_per_strip": 4,
    "countdown_seconds": 3
  }
}
```

### Usage Flow

1. Enter PIN to unlock
2. Select 4 frames (one per photo slot)
3. Start photo session
4. Take 4 photos with countdown
5. View final photostrip
6. Download, print, or retake

---

## Web Application

### Tech Stack

- **Frontend:** React 18 + Vite + TypeScript + Zustand
- **Backend:** FastAPI (Python) + Vercel Serverless
- **Styling:** FOFOBOOTH design (CSS variables)
- **Hosting:** Vercel (free tier available)

### Local Development

**Backend:**
```bash
cd api
pip install -r requirements.txt
python main.py
# API at http://localhost:8000
```

**Frontend:**
```bash
cd web
npm install
npm run dev
# App at http://localhost:5173
```

### Environment Variables

**Backend (`api/.env`):**
```bash
PIN_HASH=$2b$12$... # bcrypt hash of PIN
JWT_SECRET=your-secret-key
FRONTEND_URL=http://localhost:5173
```

**Frontend (`web/.env`):**
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

### Deployment to Vercel

See [Vercel Deployment Guide](docs/plans/2026-01-28-vercel-deployment-guide.md) for detailed instructions.

**Quick Steps:**
1. Push code to GitHub
2. Import to Vercel (backend: `api/` folder)
3. Import to Vercel (frontend: `web/` folder)
4. Set environment variables
5. Deploy!

---

## Design Language (FOFOBOOTH)

- **Colors:**
  - Background: #333333 (charcoal)
  - Accent: #FFC0CB (pastel pink)
  - Text: #FFFFFF (white)
  - Success: #4CAF50 (green)

- **Typography:**
  - Font: Montserrat/Poppins (sans-serif)
  - Uppercase headings
  - Bold weights

- **Components:**
  - Rounded corners (8-12px)
  - Subtle shadows
  - Generous spacing

---

## Frame Templates

Frame templates are PNG images with transparency. Place them in `project_files/frames/`.

### Creating Custom Frames

1. Create PNG with transparent background
2. Recommended size: 800x1000px
3. Place frame elements around a central photo area
4. Save to `project_files/frames/`

### Generating Test Frames

```bash
python scripts/generate_frames.py
```

---

## API Endpoints (Web Backend)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | Authenticate with PIN |
| `/api/v1/auth/verify` | GET | Verify JWT token |
| `/api/v1/frames` | GET | List all frames |
| `/api/v1/frames/upload` | POST | Upload new frame |
| `/api/v1/frames/{id}` | DELETE | Delete frame |
| `/api/v1/templates` | GET/POST | List/create templates |
| `/api/v1/templates/{id}` | DELETE | Delete template |
| `/api/v1/camera` | POST | Capture photo + frame |
| `/api/v1/composition` | POST | Compose photostrip |
| `/api/v1/composition/download/{id}` | GET | Download strip |

---

## Requirements

**Desktop App:**
- Python 3.8+
- PyQt5
- OpenCV
- Pillow
- NumPy
- Webcam or camera device

**Web App:**
- Python 3.11+ (backend)
- Node.js 18+ (frontend)
- Modern browser with WebRTC support

---

## Troubleshooting

**Desktop - Camera not working:**
- Check camera connection
- Try different `device_index` in config.json
- Ensure no other app is using camera

**Web - Camera access denied:**
- Allow camera permissions in browser
- Use HTTPS (automatic on Vercel)
- Try different browser

**Web - CORS errors:**
- Verify `FRONTEND_URL` matches exactly
- Check `VITE_API_URL` in frontend

**Deployment - Module not found:**
- Ensure `requirements.txt` is complete
- Check Python version (3.11+)

---

## License

MIT License - See LICENSE file for details

---

## Roadmap

- [ ] Supabase integration for cloud storage
- [ ] PWA support for offline use
- [ ] Video recording mode
- [ ] Social media sharing
- [ ] Custom branding options
- [ ] Multi-language support
