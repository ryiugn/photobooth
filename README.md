# Photobooth Application

A photobooth application with PIN authentication, per-photo frame selection, and photostrip generation. Available as both a **PyQt5 Desktop App** and a **Web Application**.

> **DEPLOYMENT POLICY:** Use **Vercel CLI** for all deployments unless errors occur. See [Deploy to Vercel](#deploy-to-vercel) for details.
>
> **IMPORTANT:** This project is primarily designed for **deployment on Vercel**, not as a local application. Deployment URLs change with each deploy. Always use the Vercel CLI to check current deployment URLs before updating environment variables.

**Repository:** https://github.com/ryiugn/photobooth

---

## Checking Deployment URLs (REQUIRED)

> **USE VERCEL CLI FOR ALL DEPLOYMENT OPERATIONS**
>
> Before updating environment variables or making API changes, always check the current deployment URLs using the Vercel CLI:

```bash
# Check API backend deployments
cd api
vercel list --yes

# Check web frontend deployments
cd ../web
vercel list --yes
```

The output shows the latest production URLs, for example:
```
> Deployments for ryiugns-projects/api

  Age     Deployment                                            Status      Environment
  19h     https://api-dbay0rn5r-ryiugns-projects.vercel.app     ● Ready     Production
```

**After any deployment, always:**
1. Run `vercel list --yes` to get the new URLs
2. Update environment variables with the new URLs
3. Redeploy if needed to propagate URL changes

See [Vercel Deployment](#deploy-to-vercel) section for details.

---

## Quick Start

Choose your platform:

### Desktop Application (PyQt5)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
cd src && python main.py
```
**Default PIN:** `1234`

### Web Application (React + FastAPI)
```bash
# Backend (Terminal 1)
cd api
pip install -r requirements.txt
python main.py

# Frontend (Terminal 2)
cd web
npm install
npm run dev
```
**Default PIN:** `1234`
**Frontend:** http://localhost:5173
**API Docs:** http://localhost:8000/docs

---

## Getting Started - Complete Setup

### Prerequisites

**For Desktop App:**
- Python 3.8 or higher
- Webcam or camera device

**For Web App:**
- Python 3.11 or higher (backend)
- Node.js 18 or higher (frontend)
- Modern web browser with WebRTC support

### Desktop Application Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/ryiugn/photobooth.git
cd photobooth
```

#### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### 3. (Optional) Generate Frame Assets
```bash
python scripts/generate_frames.py
```
This creates sample frame templates in `project_files/frames/`.

#### 4. Configure Settings (Optional)
Edit `project_files/config.json` to customize:
- PIN code
- Camera device index
- Photostrip settings

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

#### 5. Run the Application
```bash
cd src
python main.py
```

#### 6. Usage Flow
1. Enter PIN to unlock (default: `1234`)
2. Select 4 frames (one per photo slot)
3. Start photo session
4. Take 4 photos with countdown
5. View final photostrip
6. Download, print, or retake

---

### Web Application Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/ryiugn/photobooth.git
cd photobooth
```

#### 2. Backend Setup (FastAPI)

**Install dependencies:**
```bash
cd api
pip install -r requirements.txt
```

**Configure environment variables:**
```bash
# Copy example env file
cp .env.example .env
```

**Set up your environment variables:**
```bash
# 1. Generate a secure JWT secret (32+ random characters)
#    Use: https://www.random.org/strings/?num=1&len=32&digits=on&upperalpha=on&loweralpha=on&unique=on
#    Or Python: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=your-secure-random-secret-key-min-32-characters

# 2. For local development, use localhost:
FRONTEND_URL=http://localhost:5173

# 3. PIN hash below is for "1234" (default PIN - no change needed)
PIN_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7TiK.MnKHq
```

**What each variable does:**
- **JWT_SECRET:** Secret key for signing authentication tokens. Generate any random string 32+ characters.
- **FRONTEND_URL:** Where your frontend runs. Use `http://localhost:5173` for local development.
- **PIN_HASH:** Bcrypt hash of your PIN. The default is for PIN "1234" - no change needed for testing.

**Run the backend:**
```bash
python main.py
```
API will be available at:
- **API:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

#### 3. Frontend Setup (React + Vite)

**Open a new terminal and install dependencies:**
```bash
cd web
npm install
```

**Configure environment variables:**
```bash
# Copy example env file
cp .env.example .env

# Edit .env if backend is on different port
```

Default `.env`:
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

**Run the frontend:**
```bash
npm run dev
```
Frontend will be available at: **http://localhost:5173**

#### 4. Test the Web Application

1. Open http://localhost:5173
2. Enter PIN: `1234`
3. Select 4 frames
4. Allow camera permissions when prompted
5. Take photos and test photostrip generation

---

## Deploy to Vercel

> **DEPLOYMENT POLICY: USE VERCEL CLI**
>
> **ALWAYS use Vercel CLI for deployments** unless you encounter errors. The Vercel Dashboard automatic deployment is configured as a backup method only.
>
> **Reason:** Vercel CLI provides better control, immediate feedback, and proper project linking for this monorepo structure.

> **CRITICAL:** Deployment URLs change with each deployment on Vercel. After deploying, **always** use `vercel list --yes` to get the current production URLs before updating environment variables.

### Standard Deployment Procedure (Vercel CLI)

**Step 1: Deploy Backend**
```bash
cd api
vercel --prod --yes
```

**Step 2: Deploy Frontend**
```bash
cd ../web
vercel --prod --yes
```

**Step 3: Get Current Deployment URLs**
```bash
# Check API URL
cd ../api
vercel list --yes

# Check Web URL
cd ../web
vercel list --yes
```

**Step 4: Update Environment Variables if Needed**
If the deployment URLs have changed, update environment variables in Vercel Dashboard or via CLI, then redeploy.

### Checking Current Deployment URLs

**Step 1: Deploy Backend**
1. Go to https://vercel.com/new
2. Import your GitHub repository (`ryiugn/photobooth`)
3. Configure:
   - **Root Directory:** `api`
   - **Framework Preset:** Python (auto-detected)
4. Add Environment Variables:
   ```
   # Use the default PIN hash for "1234", or generate your own
   PIN_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7TiK.MnKHq

   # Generate a random 32+ character secret key
   JWT_SECRET=generate-a-random-32-character-string

   # After deploying frontend, come back and update this
   FRONTEND_URL=https://your-frontend-project-name.vercel.app
   ```
5. Click "Deploy"

**Step 2: Deploy Frontend**
1. Create another new project on Vercel
2. Import the same repository
3. Configure:
   - **Root Directory:** `web`
   - **Framework Preset:** Vite (auto-detected)
4. Add Environment Variable:
   ```
   # Use your backend URL from Step 1
   VITE_API_URL=https://your-backend-project-name.vercel.app/api/v1
   ```
5. Click "Deploy"

**Step 3: Update CORS (Important!)**
After both deployments finish:
1. Go back to your backend project on Vercel
2. Update `FRONTEND_URL` to your actual frontend domain
3. Redeploy backend

---

### Quick Reference: What Values to Use

**Local Development:**
```bash
# Backend (.env)
JWT_SECRET=any-random-string-for-local-dev-32chars
FRONTEND_URL=http://localhost:5173

# Frontend (.env)
VITE_API_URL=http://localhost:8000/api/v1
```

**Production (Vercel):**

**IMPORTANT:** URLs change with each deployment. Always check current URLs with:
```bash
# Check current API URL
cd api && vercel list --yes

# Check current Web URL
cd web && vercel list --yes
```

Then use the current production URLs:
```bash
# Backend (Vercel env vars)
JWT_SECRET=xK7mN9pL2vR8sT4wQ6yH3jF5dD8gV1nB2cM6kP (generate your own 32-char string)
FRONTEND_URL=https://<current-web-deployment>.vercel.app (your actual frontend domain)

# Frontend (Vercel env vars)
VITE_API_URL=https://<current-api-deployment>.vercel.app/api/v1 (your actual backend domain)
```

### Backup Method: Vercel Dashboard Automatic Deployment

> **ONLY use this method if Vercel CLI fails.** Vercel CLI is the recommended deployment method for this project.

```bash
# Install GitHub CLI (if not installed)
# Then:
gh auth login
gh repo set-default ryiugn/photobooth

# Deploy backend
cd api
vercel --prod

# Deploy frontend
cd ../web
vercel --prod
```

**See [Vercel Deployment Guide](docs/plans/2026-01-28-vercel-deployment-guide.md) for detailed instructions.**

---

## Project Structure

```
photobooth/
├── src/                      # Desktop App (PyQt5)
│   ├── main.py              # Desktop app entry point
│   ├── pages/               # UI pages
│   │   ├── login.py         # PIN authentication
│   │   ├── frame_selection.py   # 4-slot frame picker
│   │   ├── capture_display.py    # Camera + countdown
│   │   ├── photostrip_reveal.py  # Final result
│   │   └── template_manager.py   # Template CRUD
│   ├── widgets/             # Custom widgets
│   │   ├── frame_slot_card.py
│   │   └── frame_picker_dialog.py
│   ├── camera_handler.py    # Camera management
│   ├── frame_composer.py    # Photostrip composition
│   └── template_storage.py  # Template CRUD
│
├── api/                      # Web Backend (FastAPI)
│   ├── main.py              # Vercel serverless entry
│   ├── routes/              # API endpoints
│   │   ├── auth.py          # Authentication
│   │   ├── frames.py        # Frame CRUD
│   │   ├── templates.py     # Template operations
│   │   ├── camera.py        # Photo capture + frame
│   │   └── composition.py   # Photostrip generation
│   ├── config/              # Settings & env vars
│   ├── requirements.txt     # Python deps
│   ├── .env.example         # Environment template
│   └── vercel.json          # Vercel config
│
├── web/                      # Web Frontend (React)
│   ├── src/
│   │   ├── pages/           # React pages
│   │   │   ├── LoginPage.tsx
│   │   │   ├── FrameSelectionPage.tsx
│   │   │   ├── CameraPage.tsx
│   │   │   ├── PhotostripRevealPage.tsx
│   │   │   └── TemplateManagerPage.tsx
│   │   ├── state/           # Zustand store
│   │   ├── services/        # API service layer
│   │   ├── types/           # TypeScript types
│   │   └── main.tsx         # App entry
│   ├── package.json
│   ├── vite.config.ts
│   ├── .env.example
│   └── vercel.json
│
├── project_files/
│   ├── frames/              # Frame templates (PNG)
│   ├── templates/           # Saved templates
│   ├── captured_images/     # Desktop app output
│   ├── sessions/            # Web app temp storage
│   └── strips/              # Web app output
│
├── scripts/                  # Utility scripts
│   └── generate_frames.py   # Create sample frames
│
├── docs/
│   └── plans/               # Design & deployment docs
│       ├── 2026-01-27-web-photobooth-design.md
│       ├── 2026-01-28-vercel-deployment-guide.md
│       └── ...
│
├── requirements.txt          # Desktop app deps
└── README.md
```

---

## Features

### Desktop Application (PyQt5)
- ✅ PIN Authentication with configurable code
- ✅ 4-slot frame selection (different frame per photo)
- ✅ Template save/load functionality
- ✅ Real-time camera feed with 3-second countdown
- ✅ Photostrip generation with frame overlays
- ✅ Download, print, or retake options
- ✅ FOFOBOOTH design (dark charcoal + pastel pink)

### Web Application (React + FastAPI)
- ✅ Same features as desktop app
- ✅ Browser-based camera access (WebRTC getUserMedia)
- ✅ Responsive design for mobile and desktop
- ✅ JWT-based authentication
- ✅ Serverless API on Vercel (free tier)
- ✅ API documentation with Swagger/OpenAPI
- ✅ TypeScript for type safety
- ✅ Zustand for state management

---

## Design Language (FOFOBOOTH)

### Color Palette
```css
--color-primary: #FFC0CB;      /* Pastel pink */
--color-secondary: #333333;    /* Charcoal gray */
--color-background: #333333;   /* Dark background */
--color-text: #FFFFFF;         /* White text */
--color-text-dark: #1A0A00;    /* Dark for light backgrounds */
--color-accent: #4CAF50;       /* Green for success/selection */
--color-error: #FF6B6B;        /* Red for errors */

/* Seashell gradient for lighter pages */
--gradient-seashell: linear-gradient(135deg, #FFF8DC 0%, #FFDAB9 100%);
```

### Typography
- **Font Family:** Montserrat, Poppins (sans-serif)
- **Headings:** Uppercase, bold, letter-spaced
- **Body:** Regular weight, readable sizes

### Components
- **Border Radius:** 8-12px (rounded)
- **Spacing:** 8/12/16/24/32/48px scale
- **Shadows:** Subtle drop shadows
- **Transitions:** 0.3s ease for interactions

---

## API Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/auth/login` | POST | Authenticate with PIN | No |
| `/api/v1/auth/verify` | GET | Verify JWT token | Yes |
| `/api/v1/auth/logout` | POST | Logout (client-side) | Yes |
| `/api/v1/frames` | GET | List all frames | Yes |
| `/api/v1/frames/upload` | POST | Upload new frame | Yes |
| `/api/v1/frames/{id}` | DELETE | Delete frame | Yes |
| `/api/v1/frames/{id}/content` | GET | Get frame image | Yes |
| `/api/v1/templates` | GET/POST | List/create templates | Yes |
| `/api/v1/templates/{id}` | DELETE | Delete template | Yes |
| `/api/v1/camera` | POST | Capture photo + apply frame | Yes |
| `/api/v1/composition` | POST | Compose 4-photo strip | Yes |
| `/api/v1/composition/download/{id}` | GET | Download strip | Yes |

**Interactive API Documentation:** http://localhost:8000/docs

---

## Frame Templates

### Creating Custom Frames

Frame templates are PNG images with transparency.

**Specifications:**
- **Format:** PNG with transparency
- **Recommended Size:** 800x1000px
- **Photo Area:** Central region with transparency
- **Frame Elements:** Decorative borders, text, graphics

**Steps:**
1. Create/design your frame in any image editor
2. Ensure central area is transparent
3. Save as PNG
4. Place in `project_files/frames/`

### Generating Test Frames

```bash
python scripts/generate_frames.py
```

This creates 3 sample frames:
- `frame_simple.png` - Simple pink border
- `frame_kawaii.png` - Cute pastel design
- `frame_classic.png` - Elegant dark frame

---

## Configuration

### Desktop App (`project_files/config.json`)

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
  "output_dir": "project_files/captured_images",
  "photostrip": {
    "photos_per_strip": 4,
    "countdown_seconds": 3
  },
  "printer": {
    "enabled": true,
    "default_printer": "default"
  }
}
```

### Web Backend (`api/.env`)

```bash
# Authentication
PIN_HASH=$2b$12$... # Generate with: python -c "import bcrypt; print(bcrypt.hashpw('YOUR_PIN'.encode(), bcrypt.gensalt(12)).decode())"
JWT_SECRET=your-secret-key-min-32-characters

# CORS
FRONTEND_URL=http://localhost:5173

# File Storage (local, ephemeral on Vercel)
FRAMES_DIR=project_files/frames
TEMPLATES_DIR=project_files/templates
SESSIONS_DIR=project_files/sessions
STRIPS_DIR=project_files/strips

# Processing
MAX_PHOTO_SIZE_MB=10
PHOTO_QUALITY=95
```

### Web Frontend (`web/.env`)

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Troubleshooting

### Desktop Application

**Problem:** Camera not detected
**Solution:**
- Try different `device_index` values in config.json (0, 1, 2...)
- Ensure no other app is using the camera
- Check USB connection

**Problem:** PyQT5 not found
**Solution:**
```bash
pip install --upgrade pip
pip install PyQt5
```

**Problem:** Frames not loading
**Solution:**
```bash
python scripts/generate_frames.py
```

### Web Application

**Problem:** Camera access denied
**Solution:**
- Allow camera permissions in browser
- Use HTTPS (automatic on Vercel)
- Try different browser (Chrome, Firefox, Safari)

**Problem:** CORS errors
**Solution:**
- Verify `FRONTEND_URL` in backend matches exactly
- Check `VITE_API_URL` in frontend
- Ensure backend is running

**Problem:** Module not found on Vercel
**Solution:**
- Ensure `requirements.txt` includes all dependencies
- Check Python version (3.11+)

**Problem:** Function timeout on Vercel
**Solution:**
- Optimize image sizes
- Consider Railway/Render for longer processing
- Implement async background jobs

---

## Requirements

**Desktop App:**
- Python 3.8+
- PyQt5
- OpenCV (`opencv-python`)
- Pillow
- NumPy
- Webcam/camera device

**Web App:**
- **Backend:** Python 3.11+, FastAPI, Uvicorn
- **Frontend:** Node.js 18+, React, Vite
- **Browser:** Modern browser with WebRTC support

---

## Development

### Running Tests

**Desktop App:**
```bash
pytest tests/
```

**Web App:**
```bash
# Backend tests
cd api && pytest

# Frontend tests (TODO)
cd web && npm test
```

### Code Style

**Python:** Black, Flake8, isort

**TypeScript:** ESLint, Prettier

---

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

MIT License - See [LICENSE](LICENSE) file for details

---

## Acknowledgments

- Design inspired by [FOFOBOOTH](https://fofobooth.cc)
- Built with React, Vite, FastAPI, and PyQt5
- Deployed on Vercel

---

## Roadmap

- [ ] Supabase integration for cloud storage
- [ ] PWA support for offline use
- [ ] Video recording mode
- [ ] Social media sharing (Instagram, Facebook)
- [ ] Custom branding options
- [ ] Multi-language support
- [ ] Admin dashboard for analytics
- [ ] Email delivery of photostrips
