# Web-Based Photobooth Application - Design Document

> **Date:** 2026-01-27
> **Goal:** Transform the PyQt5 desktop photobooth into a web application accessible from anywhere
> **Architecture:** React + TypeScript frontend, FastAPI backend, Vercel hosting

---

## Table of Contents
1. [Overall Architecture](#1-overall-architecture)
2. [Frontend Architecture](#2-frontend-architecture)
3. [Backend Architecture](#3-backend-architecture)
4. [Camera & Image Processing Flow](#4-camera--image-processing-flow)
5. [Data Storage & Database](#5-data-storage--database)
6. [Deployment & Hosting](#6-deployment--hosting)
7. [Migration Strategy](#7-migration-strategy)
8. [Security Considerations](#8-security-considerations)
9. [Implementation Roadmap](#9-implementation-roadmap)

---

## 1. Overall Architecture

### Tech Stack

**Frontend:**
- React 18+ with TypeScript
- Vite (build tool)
- Material-UI or Chakra UI (component library)
- Zustand or React Context (state management)

**Backend:**
- FastAPI (Python async web framework)
- Python 3.11+
- Reuse existing code: `frame_composer.py`, `template_storage.py`
- Pydantic (data validation)

**Hosting (Vercel-based):**
- Vercel (frontend React app)
- Vercel Serverless Functions (FastAPI backend)
- Supabase (PostgreSQL + file storage)
- GitHub + CI/CD

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User's Browser                        │
│                   (Chrome, Safari, Firefox, Mobile)            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  ├─ LoginPage           │  ├─ FrameSelectionPage       │
│  ├─ CameraPage          │  ├─ TemplateManagerPage      │
│  ├─ PhotostripRevealPage│  └─ FramePicker (Modal)       │
│  └─ FOFOBOOTH UI (pink, charcoal, rounded)                  │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS API
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API Gateway (Vercel Edge)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Serverless)                │
│  ├─ /api/auth/login          │  ├─ /api/frames             │
│  ├─ /api/capture           │  ├─ /api/templates          │
│  ├─ /api/compose           │  ├─ /api/download           │
│  └─ Reuses existing code:    │                              │
│      - frame_composer.py    │  - template_storage.py      │
│      - PIL, OpenCV           │                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Supabase (PostgreSQL + Storage)                 │
│  ├─ Users (session tracking)    │  ├─ Templates               │
│  ├─ Frames (file storage)       │  ├─ Uploads                 │
│  └─ Photostrips (completed)     │  └─ Sessions                │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Authentication**
   - User enters PIN → Frontend sends POST /api/auth/login
   - Backend validates PIN hash → Returns JWT token
   - Frontend stores token in localStorage/cookies

2. **Frame Selection**
   - Frontend fetches frames from /api/frames
   - User selects 4 frames (one per photo slot)
   - Can save template via POST /api/templates
   - Can load templates from /api/templates

3. **Photo Capture**
   - Frontend requests camera via `navigator.mediaDevices.getUserMedia()`
   - Live feed displayed with frame overlay (CSS positioning)
   - On CAPTURE: Draw video to canvas → Convert to blob → POST to /api/capture
   - Backend applies corresponding frame → Returns base64 framed photo
   - Frontend displays preview → User clicks KEEP/RETAKE

4. **Photostrip Composition**
   - After 4 photos captured: Frontend sends all photo IDs to /api/compose
   - Backend calls `compose_photostrip(photos, frame_paths)`
   - Returns final photostrip image
   - Frontend displays on Photostrip Reveal page

5. **Download/Print**
   - User clicks DOWNLOAD → Frontend triggers browser download
   - User clicks PRINT → Frontend opens print dialog with image
   - Photostrip saved to Supabase storage with timestamp

---

## 2. Frontend Architecture

### Project Structure

```
web-photobooth/
├── src/
│   ├── pages/
│   │   ├── LoginPage.tsx              # PIN authentication
│   │   ├── FrameSelectionPage.tsx      # 4-frame slot selection
│   │   ├── CameraPage.tsx              # Live camera + countdown
│   │   ├── PhotostripRevealPage.tsx    # Final result + download/print
│   │   └── TemplateManagerPage.tsx     # Template CRUD
│   ├── components/
│   │   ├── FrameSlot.tsx                # Individual frame slot widget
│   │   ├── FramePickerModal.tsx         # Frame selection dialog
│   │   ├── CameraFeed.tsx               # Live camera component
│   │   ├── CountdownOverlay.tsx         # 3-2-1 countdown display
│   │   ├── PhotostripDisplay.tsx         # Final strip display
│   │   └── TemplateCard.tsx              # Template list item
│   ├── hooks/
│   │   ├── useCamera.ts                 # Camera access & permissions
│   │   ├── useAuth.ts                    # Authentication & session
│   │   ├── useTemplates.ts              # Template CRUD operations
│   │   └── useImageProcessing.ts         # Backend API calls
│   ├── services/
│   │   └── api.ts                       # Axios/fetch wrapper
│   ├── state/
│   │   └── store.ts                     # Global app state (Zustand)
│   ├── styles/
│   │   └── theme.ts                     # FOFOBOOTH theme (pink, charcoal)
│   ├── types/
│   │   └── index.ts                     # TypeScript definitions
│   └── App.tsx                          # Root component
├── public/
│   ├── frames/                          # Frame templates (PNG)
│   └── config.json                      # Frontend config
└── package.json
```

### Key Components

**FrameSlot Component:**
```tsx
interface FrameSlotProps {
  slotNumber: number;
  selectedFrame: string | null;
  onClick: () => void;
}

// Displays: "PHOTO 1", "PHOTO 2", etc.
// Shows frame thumbnail or "+" placeholder
// Green border when frame selected
// Clickable to open FramePickerModal
```

**CameraFeed Component:**
```tsx
const CameraFeed: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user' }
    })
    .then(stream => {
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    })
    .catch(err => {
      console.error("Camera access denied:", err);
      // Show error to user
    });
  }, []);

  return <video ref={videoRef} autoPlay muted playsinline />;
};
```

**State Management (Zustand):**
```typescript
interface StoreState {
  // Authentication
  isAuthenticated: boolean;
  sessionToken: string | null;

  // Frame selection
  selectedFrames: (string | null)[];
  currentSlotIndex: number;

  // Capture session
  capturedPhotos: string[];  // Base64 framed photos
  currentPhotoIndex: number;
  finalPhotostrip: string | null;

  // Templates
  templates: Template[];
}

export const useAppStore = create<StoreState>((set) => ({
  isAuthenticated: false,
  sessionToken: null,
  selectedFrames: [null, null, null, null],
  capturedPhotos: [],
  currentPhotoIndex: 0,
  finalPhotostrip: null,
  templates: [],

  setSelectedFrame: (index: number, framePath: string) => set((state) => ({
    selectedFrames: state.selectedFrames.map((f, i) =>
      i === index ? framePath : f
    )
  })),

  addCapturedPhoto: (photoBase64: string) => set((state) => ({
    capturedPhotos: [...state.capturedPhotos, photoBase64],
    currentPhotoIndex: state.currentPhotoIndex + 1
  })),

  // ... other actions
}));
```

### Styling (FOFOBOOTH Theme)

**Color Palette:**
```css
:root {
  --color-primary: #FFC0CB;      /* Pastel pink */
  --color-secondary: #333333;    /* Charcoal gray */
  --color-background: #FFF8DC;   /* Seashell */
  --color-text: #FFFFFF;         /* White */
  --color-accent: #4CAF50;       /* Green for selection */
  --border-radius: 12px;
}
```

**Button Styling:**
```css
.btn-primary {
  background: linear-gradient(180deg, #FFE4C4, #FFDAB9);
  color: #1A0A00;
  font-size: 18px;
  font-weight: bold;
  border: 2px solid #1A0A00;
  border-radius: 12px;
  padding: 15px 30px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background: linear-gradient(180deg, #FFDAB9, #FFCBA4);
}

.btn-primary:disabled {
  background: rgba(200, 180, 160, 0.5);
  color: rgba(26, 10, 0, 0.5);
  cursor: not-allowed;
}
```

---

## 3. Backend Architecture

### Project Structure

```
api/
├── main.py                     # FastAPI app entry point
├── config/
│   ├── settings.py             # Environment configuration
│   └── security.py             # Security settings (CORS, rate limiting)
├── routes/
│   ├── auth.py                  # Authentication endpoints
│   ├── frames.py                # Frame CRUD + upload
│   ├── templates.py             # Template CRUD operations
│   ├── camera.py                # Photo capture endpoint
│   ├── composition.py           # Photostrip composition
│   └── download.py              # Photostrip download
├── services/
│   ├── auth_service.py          # PIN validation, JWT management
│   ├── frame_service.py         # Frame storage/retrieval
│   ├── template_service.py      # Template operations
│   ├── composition_service.py   # Calls frame_composer.py
│   └── storage_service.py       # File system operations
├── models/
│   ├── auth.py                  # Login request/response models
│   ├── frames.py                # Frame data models
│   ├── templates.py               # Template data models
│   └── responses.py              # API response models
└── utils/
      ├── frame_composer.py      # Reused from desktop app
      ├── template_storage.py     # Reused from desktop app
      └── image_processor.py      # PIL/OpenCV utilities
```

### API Endpoints

**Authentication:**
```python
POST /api/v1/auth/login
Request: { "pin": "1234" }
Response: { "access_token": "jwt_token", "expires_in": 1800 }

POST /api/v1/auth/logout
Headers: Authorization: Bearer {token}
Response: { "message": "Logged out successfully" }

GET /api/v1/auth/verify
Headers: Authorization: Bearer {token}
Response: { "valid": true, "session_id": "uuid" }
```

**Frames:**
```python
GET /api/v1/frames
Response: {
  "frames": [
    { "id": "frame1", "name": "Classic", "url": "https://..." },
    { "id": "frame2", "name": "Kawaii", "url": "https://..." }
  ]
}

POST /api/v1/frames/upload
Request: FormData { file: (binary) }
Response: { "id": "frame_custom", "name": "Custom", "url": "https://..." }

DELETE /api/v1/frames/{frame_id}
Response: { "message": "Frame deleted" }
```

**Templates:**
```python
GET /api/v1/templates
Response: {
  "templates": [
    {
      "id": "tpl_1",
      "name": "My Mix",
      "frames": ["frame1.png", "frame2.png", "frame3.png", "frame4.png"],
      "created": "2026-01-27T14:30:00Z"
    }
  ]
}

POST /api/v1/templates
Request: {
  "name": "My Template",
  "frames": ["frame1.png", "frame2.png", "frame3.png", "frame4.png"]
}
Response: { "id": "tpl_2", "message": "Template saved" }

DELETE /api/v1/templates/{template_id}
Response: { "message": "Template deleted" }
```

**Capture & Composition:**
```python
POST /api/v1/capture
Request: FormData {
  "photo": (binary),
  "frame_index": 0,
  "session_id": "uuid"
}
Response: {
  "photo_id": "photo_abc123",
  "framed_photo": "data:image/png;base64,..."
}

POST /api/v1/compose
Request: {
  "session_id": "uuid",
  "photo_ids": ["photo_abc", "photo_def", "photo_123", "photo_456"]
}
Response: {
  "strip_id": "strip_xyz789",
  "photostrip_url": "https://storage.../strip.png",
  "photostrip_base64": "data:image/png;base64,..."
}

GET /api/v1/download/{strip_id}
Response: Binary PNG file
```

### Reusing Existing Code

**frame_composer.py Integration:**
```python
# In composition_service.py
from utils.frame_composer import compose_photostrip, apply_frame

def compose_photostrip(photos: list[bytes], frame_paths: list[str]) -> bytes:
    """
    Compose photostrip from uploaded photos.

    Args:
        photos: List of photo bytes (BGR from frontend)
        frame_paths: List of paths to frame PNGs

    Returns:
        Composed photostrip as bytes (PNG format)
    """
    # Convert bytes to numpy arrays
    import numpy as np
    import cv2
    from PIL import Image

    photo_arrays = []
    for photo_bytes in photos:
        # Convert to numpy array
        nparr = np.frombuffer(photo_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        photo_arrays.append(img)

    # Call existing composer
    result = compose_photostrip(photo_arrays, frame_paths)

    # Convert PIL Image back to bytes
    img_bytes = io.BytesIO()
    result.save(img_bytes, format='PNG')
    return img_bytes.getvalue()
```

**template_storage.py Integration:**
```python
# In template_service.py
from utils.template_storage import Template, TemplateStorage
from storage_service import download_frame

class TemplateService:
    def create_template(self, name: str, frame_ids: list[str]) -> str:
        """Create template from frame IDs."""
        frame_paths = [download_frame(fid) for fid in frame_ids]
        template = Template(
            name=name,
            frame_paths=frame_paths,
            created=datetime.now().isoformat()
        )
        storage = TemplateStorage()
        return storage.save(template)
```

---

## 4. Camera & Image Processing Flow

### Frontend Camera Access

**Permission Request:**
```typescript
const requestCameraPermission = async (): Promise<boolean> => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'user',      // Front camera for selfies
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    });

    // Success - store stream
    cameraStreamRef.current = stream;
    return true;
  } catch (err) {
    if (err.name === 'NotAllowedError') {
      setError("Camera access denied. Please allow camera permissions.");
    } else if (err.name === 'NotFoundError') {
      setError("No camera found on this device.");
    } else {
      setError(`Camera error: ${err.message}`);
    }
    return false;
  }
};
```

**Live Feed Display with Frame Overlay:**
```tsx
const CameraFeed: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const selectedFrame = useAppStore(state => state.selectedFrames[state.currentPhotoIndex]);

  // Apply frame overlay using CSS
  const frameOverlayStyle = useMemo(() => ({
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    pointerEvents: 'none',
    backgroundImage: selectedFrame ? `url(${selectedFrame})` : 'none',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    opacity: 0.8,
    zIndex: 10
  }), [selectedFrame]);

  return (
    <div className="camera-container">
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className="camera-feed"
      />
      {selectedFrame && <div style={frameOverlayStyle} />}
      <CountdownOverlay />
    </div>
  );
};
```

### Capture Process

**Frontend:**
```typescript
const capturePhoto = async (photoIndex: number): Promise<string> => {
  const video = videoRef.current;
  const canvas = document.createElement('canvas');

  // Set canvas size to match video
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const ctx = canvas.getContext('2d');

  // Apply frame overlay if present
  if (selectedFrame) {
    const frameImg = await loadImage(selectedFrame);
    ctx.drawImage(frameImg, 0, 0, canvas.width, canvas.height);
  }

  // Draw video frame
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  // Convert to blob
  return new Promise((resolve) => {
    canvas.toBlob(async (blob) => {
      const formData = new FormData();
      formData.append('photo', blob!, `photo_${photoIndex}.png`);
      formData.append('frame_index', photoIndex.toString());
      formData.append('session_id', sessionId);

      // Send to backend
      const response = await fetch('/api/v1/capture', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Capture failed');
      }

      const result = await response.json();
      resolve(result.framed_photo); // Base64 image
    }, 'image/png');
  });
};
```

**Backend Capture Handler:**
```python
@router.post("/capture")
async def capture_photo(
    photo: UploadFile = File(...),
    frame_index: int = Form(...),
    session_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Capture photo and apply frame overlay."""
    # Save temporary photo
    photo_path = await storage_service.save_temp_photo(session_id, frame_index, photo.file)

    # Get frame path for this index
    session = session_service.get_session(session_id)
    frame_path = session['selected_frames'][frame_index]

    # Apply frame using existing composer
    framed_photo = await apply_frame_async(photo_path, frame_path)

    return {
        "photo_id": f"photo_{session_id}_{frame_index}",
        "framed_photo": pil_to_base64(framed_photo)
    }

async def apply_frame_async(photo_path: str, frame_path: str) -> Image.Image:
    """Async wrapper for apply_frame."""
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, apply_frame, photo_path, frame_path)
```

### Countdown Timer

**Frontend:**
```typescript
const CountdownOverlay: React.FC = () => {
  const [countdown, setCountdown] = useState(3);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    if (isActive && countdown > 0) {
      const timer = setTimeout(() => setCountdown(c => c - 1), 1000);
      return () => clearTimeout(timer);
    } else if (isActive && countdown === 0) {
      // Capture photo
      capturePhoto(currentPhotoIndex);
      setIsActive(false);
      setCountdown(3); // Reset for next
    }
  }, [isActive, countdown]);

  return (
    isActive && (
      <div className="countdown-overlay">
        <div className="countdown-number">{countdown}</div>
      </div>
    )
  );
};
```

---

## 5. Data Storage & Database

### File Storage Structure

```
project_files/
├── frames/              # Frame templates (PNG with transparency)
│   ├── classic.png
│   ├── kawaii.png
│   ├── simple.png
│   └── ...
├── uploads/             # User-uploaded custom frames
│   ├── custom_20250127_143052_abc123.png
│   └── ...
├── templates/           # Saved template JSON files
│   ├── my_mix_20250127_140830.json
│   └── ...
├── sessions/            # Temporary session data
│   └── {session_id}/
│       ├── photo_0.png
│       ├── photo_1.png
│       ├── photo_2.png
│       └── photo_3.png
├── strips/              # Completed photostrips
│   ├── photostrip_20250127_150233_session123.png
│   └── ...
└── config.json         # App configuration
```

### Supabase Database Schema

```sql
-- Users table (for session tracking)
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    selected_frames JSONB NOT NULL DEFAULT '[]',
    current_photo_index INTEGER DEFAULT 0,
    photos_captured JSONB DEFAULT '[]',
    strip_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Templates table
CREATE TABLE templates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    frame_paths JSONB NOT NULL,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_frames CHECK (jsonb_array_length(frame_paths) = 4)
);

-- Capture sessions
CREATE TABLE capture_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    photo_0_path TEXT,
    photo_1_path TEXT,
    photo_2_path TEXT,
    photo_3_path TEXT,
    composed_strip_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_sessions_id ON capture_sessions(session_id);
CREATE INDEX idx_templates_created ON templates(created_at DESC);
```

### Storage Service Integration

**Supabase Storage Client:**
```python
from supabase import create_client

class StorageService:
    def __init__(self):
        self.supabase = create_client(
            url=os.getenv("SUPABASE_URL"),
            key=os.getenv("SUPABASE_KEY")
        )

    async def upload_frame(self, file_data: bytes, filename: str) -> str:
        """Upload frame to Supabase storage."""
        path = f"frames/{filename}"
        result = self.supabase.storage.from_(file_data).upload(path)
        return result.public_url

    async def save_temp_photo(self, session_id: str, index: int, file_data: bytes) -> str:
        """Save temporary photo to session folder."""
        path = f"sessions/{session_id}/photo_{index}.png"
        result = self.supabase.storage.from_(file_data).upload(path)
        return result.public_url

    async def save_photostrip(self, session_id: str, photostrip_bytes: bytes, filename: str) -> str:
        """Save completed photostrip."""
        path = f"strips/{filename}"
        result = self.supabase.storage.from_(photostrip_bytes).upload(path)
        return result.public_url
```

---

## 6. Deployment & Hosting (Vercel)

### Frontend Deployment (Vercel)

**vercel.json Configuration:**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install",
  "framework": "vite",
  "env": {
    "VITE_API_URL": "@api_url"
  }
}
```

**Deployment Steps:**
1. Connect GitHub repo to Vercel
2. Vercel auto-detects React + Vite
3. Configure environment variables:
   - `VITE_API_URL`: Backend API URL
   - `VITE_PIN_HASH`: Bcrypt hashed PIN (optional)
4. Deploy on push to `main` branch

**Automatic HTTPS:**
- Free SSL certificate via Let's Encrypt
- Custom domain support
- Edge caching for static assets

### Backend Deployment (Vercel Serverless Functions)

**api/index.py:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from routes import auth, frames, templates, camera, composition, download
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(frames.router, prefix="/api/v1/frames")
# ... other routers
```

**requirements.txt for Vercel Python:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.5
pillow==10.0.0
numpy==1.24.3
opencv-python==4.8.0.76
supabase==2.3.4
pydantic==2.5.0
python-jose[cryptography]==3.3.0
```

### Supabase Setup

**Create Supabase Project:**
1. Go to supabase.com
2. Create new project
3. Get credentials:
   - Project URL
   - Anon key
   - Database connection string
4. Run SQL schema script in SQL editor
5. Create storage buckets:
   - `frames`
   - `uploads`
   - `sessions`
   - `strips`

**Environment Variables (Vercel):**
```
# Backend
DATABASE_URL=postgresql://...
SUPABASE_URL=https://*.supabase.co
SUPABASE_KEY=eyJhbGci...

# Frontend
VITE_API_URL=https://api.yourdomain.com

# App Config
PIN_HASH=bcrypt_hashed_1234
FRONTEND_URL=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com
```

### CI/CD Pipeline

**GitHub Actions Workflow:**
```yaml
name: Deploy Web Photobooth

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: your-team-id
          vercel-project-name: web-photobooth
          working-directory: ./api
          vercel-args: '--prod'

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: your-team-id
          working-directory: ./web
```

---

## 7. Migration Strategy

### Phase 1: Planning & Setup (Week 1-2)

**Tasks:**
- [ ] Create new GitHub repo: `web-photobooth`
- [ ] Initialize React + Vite + TypeScript
- [ ] Set up FastAPI backend structure
- [ ] Create Vercel projects (frontend + backend)
- [ ] Set up Supabase project
- [ ] Configure local development environment
- [ ] Set up ESLint, Prettier, TypeScript configs
- [ ] Create git `.gitignore` for web project

**Deliverables:**
- Basic project structure
- Working local development environment
- Deployment platforms configured

### Phase 2: Backend Core (Week 3-4)

**Tasks:**
- [ ] Port authentication logic (PIN validation)
  - Create JWT token generation
  - Implement `/api/v1/auth/login`
- [ ] Create frame management APIs
  - GET /api/v1/frames (list from Supabase)
  - POST /api/v1/frames/upload
  - DELETE /api/v1/frames/{id}
- [ ] Port `template_storage.py` → template service
  - GET /api/v1/templates
  - POST /api/v1/templates
  - DELETE /api/v1/templates/{id}
- [ ] Create `/api/v1/capture` endpoint
  - Receive photo multipart upload
  - Apply frame using `frame_composer.py`
  - Return framed photo as base64
- [ ] Create `/api/v1/compose` endpoint
  - Accept 4 photo IDs
  - Call `compose_photostrip()`
  - Return final photostrip
- [ ] Implement `/api/v1/download/{id}` endpoint
  - Serve completed photostrip for download
- [ ] Set up Supabase storage integration
- [ ] Add CORS middleware
- [ ] Add rate limiting (5 attempts per PIN)

**Deliverables:**
- Complete backend API with all endpoints
- Authentication working
- Frame upload/download working
- Template CRUD working
- Photo capture and composition working

### Phase 3: Frontend Foundation (Week 5-6)

**Tasks:**
- [ ] Implement LoginPage component
  - PIN input (numeric keypad)
  - JWT token storage
  - Error handling
- [ ] Create API service layer
  - Axios/fetch wrapper
  - Request/response interceptors
  - Error handling
- [ ] Set up state management (Zustand)
  - Auth store
  - Frame selection store
  - Capture session store
- [ ] Create FrameSlot component
  - Display frame or placeholder
  - Click to open FramePicker
  - Green border when filled
- [ ] Create FramePickerModal component
  - Grid of frame thumbnails
  - Frame upload option
  - Search/filter frames
- [ ] Build FrameSelectionPage
  - 4 frame slots layout
  - Save/load template buttons
  - Upload frames button
  - Navigation logic

**Deliverables:**
- Login page working
- Frame selection with 4 slots working
- Template save/load functionality
- Frame upload working

### Phase 4: Camera Integration (Week 7)

**Tasks:**
- [ ] Implement CameraFeed component
  - getUserMedia() integration
  - Permission handling
  - Error states (no camera, denied access)
- [ ] Create CountdownOverlay component
  - 3-2-1 countdown timer
  - Overlay positioning (z-index)
  - Animation
- [ ] Build CameraPage
  - Live camera feed
  - Frame overlay (CSS positioning)
  - CAPTURE button
  - Progress indicator ("Photo 1 of 4")
- [ ] Implement photo capture flow
  - Capture from canvas
  - Send to backend
  - Display preview
  - KEEP & NEXT / RETAKE buttons
- [ ] Test on multiple devices (iOS, Android, desktop)

**Deliverables:**
- Camera access working on all devices
- Countdown timer functional
- Photo capture working
- Frame overlay in live feed and captured photos

### Phase 5: Photostrip Reveal (Week 7-8)

**Tasks:**
- [ ] Build PhotostripRevealPage
  - Display final photostrip
  - DOWNLOAD button (browser download)
  - PRINT button (print dialog)
  - RETAKE button (back to frame selection)
- [ ] Implement composition flow
  - Wait for 4 photos
  - Call `/api/v1/compose`
  - Display result
- [ ] Add download functionality
  - Browser native download
  - Filename with timestamp
- [ ] Add print functionality
  - Open print dialog
  - Mobile-friendly (no native print on mobile)
- [ ] Test full end-to-end flow

**Deliverables:**
- Complete photostrip generation
- Download working
- Print working
- Full app functional

### Phase 6: Polish & Optimization (Week 8-9)

**Tasks:**
- [ ] Optimize image sizes
  - Compose at reasonable resolution (e.g., 1200px wide)
  - Optimize for web delivery
  - Lazy loading for frames
- [ ] Add loading states
  - Skeleton screens
  - Loading spinners
  - Progress indicators
- [ ] Error handling
  - User-friendly error messages
  - Retry mechanisms
  - Fallback options
- [ ] Mobile optimization
  - Touch-friendly buttons
  - Responsive design
  - PWA features (install prompt, offline mode)
- [ ] Performance optimization
  - Code splitting
  - Image optimization
  - Bundle size optimization

**Deliverables:**
- Production-ready web app
- Mobile-optimized
- Fast loading
- Good UX

### Phase 7: Testing & Bug Fixes (Week 9)

**Tasks:**
- [ ] Unit tests (Vitest + React Testing Library)
- [ ] Integration tests (API endpoints)
- [ ] E2E tests (Playwright/Cypress)
  - Full capture flow
  - Template save/load
  - Download/print
- [ ] Cross-browser testing
  - Chrome, Safari, Firefox, Edge
  - iOS Safari, Android Chrome
- [ ] Load testing
  - Concurrent users
  - Heavy image uploads
- [ ] Bug fixes and polish
- [ ] Accessibility audit
  - Keyboard navigation
  - Screen reader support
  - ARIA labels

**Deliverables:**
- Comprehensive test coverage
- Browser compatibility verified
- Performance tested
- Accessibility compliant
- Known issues resolved

### Phase 8: Deployment (Week 10)

**Tasks:**
- [ ] Configure custom domain
- [ ] Set up production database
- [ ] Configure environment variables
- [ ] Set up monitoring (Sentry for error tracking)
- [ ] Deploy backend to Vercel serverless
- [ ] Deploy frontend to Vercel
- [ ] Set up CI/CD pipeline
- [ ] Test production deployment
- [ ] Create user documentation
- [ ] Beta testing with small group

**Deliverables:**
- Live web application
- Complete documentation
- Support guide
- Beta test results

---

## 8. Security Considerations

### Authentication & Session Security

**PIN Storage:**
```python
# Never store PIN in plaintext
# Use bcrypt with high work factor
import bcrypt

PIN_HASH = bcrypt.hashpw(PIN.encode('utf-8'), bcrypt.gensalt(log rounds=12))
```

**JWT Token Configuration:**
```python
from datetime import timedelta
from jose import jwt

SECRET_KEY = os.getenv("JWT_SECRET", os.urandom(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

**Session Management:**
```python
# Invalidate tokens after photostrip completion
# Clean up temporary files after 24 hours
async def cleanup_old_sessions():
    cutoff = datetime.now() - timedelta(hours=24)
    # Delete sessions older than 24 hours
    await database.execute(
        "DELETE FROM capture_sessions WHERE created_at < $1",
        cutoff
    )
```

### Input Validation

**Pydantic Models:**
```python
from pydantic import BaseModel, Field, validator

class LoginRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=6)

    @validator('pin')
    def validate_pin(cls, v):
        if not v.isdigit():
            raise ValueError('PIN must be numeric')
        return v

class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    frames: list[str] = Field(..., min_items=4, max_items=4)

    @validator('frames')
    def validate_frames(cls, v):
        for frame_path in v:
            if not Path(frame_path).exists():
                raise ValueError(f"Frame not found: {frame_path}")
        return v
```

### File Upload Security

**Upload Validation:**
```python
import magic

async def validate_upload(file: UploadFile):
    # Check file size (max 10MB)
    MAX_SIZE = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise ValueError("File too large. Maximum size: 10MB")
    await file.seek(0)

    # Validate file type
    file_type = magic.from_buffer(content, mime=True)
    allowed_types = ['image/png', 'image/jpeg', 'image/webp']
    if file_type not in allowed_types:
        raise ValueError(f"Invalid file type: {file_type}")

    # Check for malicious content (basic)
    if b'<script' in content.lower()[:1000]:  # Check first 1000 bytes
        raise ValueError("Potentially malicious file detected")

    return file
```

### Rate Limiting

**SlowAPI Rate Limiter:**
```python
from slowapi import Limiter, HTTPException

auth_limiter = Limiter(key_func=get_remote_address, max_attempts=5, seconds=300)

@app.post("/api/v1/auth/login")
@auth_limiter
async def login(request: Request):
    # Check rate limit
    # Validate PIN
    # Return token
    pass

if isinstance(auth_limiter._slowapi_rate_limit_exceeded, HTTPException):
    raise HTTPException(
        status_code=429,
        detail="Too many attempts. Please wait 5 minutes."
    )
```

### CORS Configuration

**Vercel-Specific CORS:**
```python
# Frontend URL
ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "http://localhost:3000",  # Local dev
    "http://localhost:5173"   # Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
```

### Data Privacy

**Photostrip Storage:**
```python
# Auto-cleanup old files
@cron_job(hourly)
async def cleanup_old_strips():
    # Delete strips older than 7 days
    cutoff = datetime.now() - timedelta(days=7)
    await storage.delete_old_files(cutoff)
    logger.info(f"Deleted {count} old strips")
```

**No Personal Data:**
- No names, emails, or identifying info collected
- Session IDs are random UUIDs
- No tracking pixels or analytics
- Automatic data expiration

---

## 9. Implementation Roadmap

### Timeline Overview

| Week | Phase | Key Deliverables |
|------|-------|----------------|
| 1-2 | Planning & Setup | Project structure, dev environment, hosting configured |
| 3-4 | Backend Core | Authentication API, frame/upload, templates, capture, composition |
| 5-6 | Frontend Core | Login, frame selection, camera integration |
| 7 | Camera & Capture | Camera feed, countdown, photo capture flow |
| 8 | Polish & Optimize | Photostrip reveal, download, print, performance |
| 9 | Testing & Fixes | Unit tests, E2E tests, cross-browser, bug fixes |
| 10 | Deployment & Launch | Production deployment, documentation, beta test |

### Week 1-2: Planning & Setup

**Setup Tasks:**
- [ ] Initialize GitHub repository: `web-photobooth`
- [ ] Create frontend: `npm create vite@latest web-photobooth --template react-ts`
- [ ] Create backend: `mkdir api && cd api && python -m venv venv && source venv/bin/activate`
- [ ] Install frontend deps: `npm install axios zustand @types/react`
- [ ] Install backend deps: `pip install fastapi uvicorn[standard]`
- [ ] Set up Vercel CLI: `npm install -g vercel`
- [ ] Set up Supabase project
- [ ] Configure environment variables locally

**Commit:** `chore: project initialized with frontend and backend`

### Week 3-4: Backend Core

**Authentication:**
```
[ ] api/routes/auth.py
    - POST /api/v1/auth/login
    - GET /api/v1/auth/verify
    - JWT token generation/validation
```

**Frames:**
```
[ ] api/routes/frames.py
    - GET /api/v1/frames - list all frames
    - POST /api/v1/frames/upload - upload custom frame
    - DELETE /api/v1/frames/{id} - delete frame
```

**Templates:**
```
[ ] api/routes/templates.py
    - GET /api/v1/templates - list templates
    - POST /api/v1/templates - create template
    - DELETE /api/v1/templates/{id} - delete template
```

**Capture & Composition:**
```
[ ] api/routes/camera.py
    - POST /api/v1/capture - receive photo, apply frame
    [ ] api/routes/composition.py
    - POST /api/v1/compose - compose 4-photo strip
```

**Commit:** `feat: implement core backend APIs`

### Week 5-6: Frontend Foundation

**Login Page:**
```
[ ] src/pages/LoginPage.tsx
    - Numeric keypad for PIN entry
    - Login button
    - Error handling
```

**Frame Selection:**
```
[ ] src/pages/FrameSelectionPage.tsx
    - 4 FrameSlot components
    - FramePickerModal
    - Template save/load
```

**API Integration:**
```
[ ] src/services/api.ts
    - Axios configuration
    - API methods
    - Error handling
```

**Commit:** `feat: implement login and frame selection UI`

### Week 7: Camera Integration

```
[ ] src/components/CameraFeed.tsx
    - getUserMedia integration
    - Permission handling
    - Error states
[ ] src/components/CountdownOverlay.tsx
    - 3-2-1 countdown
    - Overlay positioning
[ ] src/pages/CameraPage.tsx
    - Live feed with frame overlay
    - CAPTURE button
    - Progress indicator
    - Photo preview
```

**Commit:** `feat: implement camera capture flow`

### Week 8: Polish & Optimize

```
[ ] src/pages/PhotostripRevealPage.tsx
    - Display final photostrip
    - Download button
    - Print button
    - Retake button
[ ] Performance optimization
    - Code splitting
    - Image optimization
    - Lazy loading
[ ] Error handling
    - User-friendly messages
    - Retry mechanisms
[ ] Mobile optimization
    - Responsive design
    - Touch-friendly
```

**Commit:** `feat: complete photostrip reveal and optimization`

### Week 9: Testing & Bug Fixes

```
[ ] Unit tests (Vitest)
[ ] Integration tests (API)
[ ] E2E tests (Playwright)
[ ] Cross-browser testing
[ ] Load testing
[ ] Bug fixes
[ ] Accessibility audit
```

**Commit:** `test: comprehensive test suite and bug fixes`

### Week 10: Deployment

```
[ ] Configure custom domain
[ ] Set up production database
[ ] Deploy to Vercel
[ ] Set up CI/CD
[ ] Create user documentation
[ ] Beta testing
[ ] Bug fixes
[ ] Final deployment
```

**Commit:** `release: version 1.0.0 launch`

---

## File Structure Summary

**Complete Web Project Structure:**
```
web-photobooth/
├── api/                               # FastAPI backend
│   ├── main.py
│   ├── requirements.txt
│   ├── routes/
│   │   ├── auth.py
│   │   ├── frames.py
│   │   ├── templates.py
│   │   ├── camera.py
│   │   ├── composition.py
│   │   └── download.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── frame_service.py
│   │   ├── template_service.py
│   │   └── storage_service.py
│   ├── models/
│   │   ├── auth.py
│   │   ├── frames.py
│   │   └── templates.py
│   ├── utils/
│   │   ├── frame_composer.py    # Reused from desktop app
│   │   ├── template_storage.py   # Reused from desktop app
│   │   └── image_processor.py
│   └── config/
│       └── settings.py
│
├── web/                               # React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── FrameSelectionPage.tsx
│   │   │   ├── CameraPage.tsx
│   │   │   ├── PhotostripRevealPage.tsx
│   │   │   └── TemplateManagerPage.tsx
│   │   ├── components/
│   │   │   ├── FrameSlot.tsx
│   │   │   ├── FramePickerModal.tsx
│   │   │   ├── CameraFeed.tsx
│   │   │   ├── CountdownOverlay.tsx
│   │   │   ├── PhotostripDisplay.tsx
│   │   │   └── TemplateCard.tsx
│   │   ├── hooks/
│   │   │   ├── useCamera.ts
│   │   │   ├── useAuth.ts
│   │   │   ├── useTemplates.ts
│   │   │   └── useImageProcessing.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── state/
│   │   │   └── store.ts
│   │   ├── styles/
│   │   │   └── theme.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── App.tsx
│   ├── public/
│   │   └── frames/           # Frame templates
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── index.html
│   └── vercel.json
│
├── docs/                               # Documentation
│   └── plans/
│       └── 2026-01-27-web-photobooth-design.md
│
├── .github/
│   └── workflows/
│       └── deploy.yml         # CI/CD pipeline
│
└── README.md                           # Project documentation
```

---

## Tools & Resources

**Development Tools:**
- **Frontend**: React, TypeScript, Vite
- **Backend**: FastAPI, Python 3.11+
- **Database**: Supabase (PostgreSQL)
- **Hosting**: Vercel
- **Version Control**: Git + GitHub

**External Dependencies:**
- PyPI (backend packages)
- npm (frontend packages)
- Supabase (database + storage)

**Documentation:**
- React docs: https://react.dev/
- FastAPI docs: https://fastapi.tiangolo.com/
- Vercel docs: https://vercel.com/docs
- Supabase docs: https://supabase.com/docs

---

**Design Complete** ✅

This design document provides a complete roadmap for transforming the PyQt5 desktop photobooth into a web application. The architecture prioritizes:
- **User Experience**: Clean, intuitive interface
- **Accessibility**: Works on any device with a browser
- **Maintainability**: Clean code, reusable components
- **Scalability**: Handles multiple concurrent users
- **Cost-Effective**: Free tiers and affordable hosting

**Next Steps:**
1. Review and approve design
2. Initialize project structure
3. Start with backend development (Week 3-4)
4. Iterate through all phases

Ready for implementation?
