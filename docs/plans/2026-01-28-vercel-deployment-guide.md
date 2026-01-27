# Web Photobooth - Vercel Deployment Guide

> **Date:** 2026-01-28
> **Goal:** Deploy the web photobooth application to Vercel with FastAPI backend and React frontend

---

## Overview

This guide covers deploying the Web Photobooth application to Vercel using:
- **Frontend:** React + Vite + TypeScript hosted on Vercel Edge Network
- **Backend:** FastAPI serverless functions on Vercel
- **Storage:** Local file storage (can be upgraded to Supabase)

---

## Prerequisites

1. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
2. **GitHub Account** - For Vercel CI/CD integration
3. **Python 3.11+** - For local development
4. **Node.js 18+** - For frontend development

---

## Project Structure

```
chai proj/
├── api/                    # FastAPI Backend
│   ├── main.py            # Entry point for Vercel serverless
│   ├── config/            # Configuration
│   ├── routes/            # API endpoints
│   │   ├── auth.py        # Authentication
│   │   ├── frames.py      # Frame CRUD
│   │   ├── templates.py   # Template CRUD
│   │   ├── camera.py      # Photo capture
│   │   └── composition.py # Photostrip generation
│   ├── requirements.txt   # Python dependencies
│   └── vercel.json        # Vercel configuration
│
├── web/                    # React Frontend
│   ├── src/
│   │   ├── pages/         # Page components
│   │   ├── state/         # Zustand store
│   │   ├── services/      # API service
│   │   └── types/         # TypeScript types
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── vercel.json
│
└── docs/
    └── plans/
        └── 2026-01-28-vercel-deployment-guide.md
```

---

## Environment Variables

### Backend Environment Variables

Set these in Vercel dashboard or `.env` locally:

```bash
# Authentication
PIN_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7TiK.MnKHq  # Default: "1234"
JWT_SECRET=your-secret-key-change-in-production

# CORS
FRONTEND_URL=https://your-domain.vercel.app

# Storage (optional - for Supabase integration)
# SUPABASE_URL=https://*.supabase.co
# SUPABASE_KEY=your-anon-key
```

### Frontend Environment Variables

```bash
VITE_API_URL=https://your-api-domain.vercel.app/api/v1
```

---

## Local Development

### Backend Development

1. **Install Python dependencies:**
   ```bash
   cd api
   pip install -r requirements.txt
   ```

2. **Run the FastAPI server locally:**
   ```bash
   python main.py
   ```

   API will be available at `http://localhost:8000`

3. **Test the API:**
   - Open `http://localhost:8000/docs` for interactive API documentation
   - Test authentication: `POST /api/v1/auth/login` with `{"pin": "1234"}`

### Frontend Development

1. **Install Node dependencies:**
   ```bash
   cd web
   npm install
   ```

2. **Start the Vite dev server:**
   ```bash
   npm run dev
   ```

   Frontend will be available at `http://localhost:5173`

3. **The Vite dev server proxies API requests** to the backend

---

## Vercel Deployment

### Step 1: Prepare Your Repository

1. **Ensure all code is committed to Git:**
   ```bash
   git add .
   git commit -m "feat: initial web photobooth implementation"
   ```

2. **Push to GitHub:**
   ```bash
   git push origin main
   ```

### Step 2: Deploy Backend to Vercel

1. **Go to [vercel.com](https://vercel.com) and click "New Project"**

2. **Import your GitHub repository**

3. **Configure the project:**
   - **Root Directory:** `api`
   - **Framework Preset:** Python (detected automatically)
   - **Build Command:** (leave empty for serverless)
   - **Output Directory:** (leave empty)

4. **Set Environment Variables:**
   - `PIN_HASH`: Copy from Vercel dashboard or use default
   - `JWT_SECRET`: Generate a secure random string
   - `FRONTEND_URL`: Your frontend domain (e.g., `photobooth-web.vercel.app`)

5. **Deploy!**
   - Vercel will build and deploy the API
   - Note the deployed API URL (e.g., `photobooth-api.vercel.app`)

### Step 3: Deploy Frontend to Vercel

1. **Create another new project in Vercel**

2. **Import the same GitHub repository**

3. **Configure the project:**
   - **Root Directory:** `web`
   - **Framework Preset:** Vite (detected automatically)
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

4. **Set Environment Variables:**
   - `VITE_API_URL`: Your backend API URL + `/api/v1`
     - Example: `https://photobooth-api.vercel.app/api/v1`

5. **Deploy!**
   - Vercel will build the React app and deploy to Edge Network

---

## Post-Deployment Configuration

### 1. Generate a Secure PIN Hash

The default PIN is "1234". To change it:

```python
import bcrypt

pin = "YOUR_NEW_PIN"
pin_hash = bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt(12))
print(pin_hash.decode('utf-8'))
```

Set the output as `PIN_HASH` in Vercel environment variables.

### 2. Configure CORS

Ensure the backend's `FRONTEND_URL` matches your deployed frontend URL.

### 3. Test the Deployment

1. Visit your frontend URL
2. Enter PIN: `1234`
3. Select frames
4. Take photos
5. Verify photostrip generation works

---

## Troubleshooting

### "Module not found" Errors

**Issue:** Vercel can't find a module

**Solution:** Ensure `requirements.txt` includes all dependencies:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.5
Pillow==10.1.0
numpy==1.24.3
opencv-python==4.8.1.78
python-jose[cryptography]==3.3.0
```

### "CORS" Errors

**Issue:** Frontend can't access API

**Solution:**
- Verify `FRONTEND_URL` matches exactly (including https://)
- Check Vercel deployment logs for CORS errors

### "Function Execution Timed Out"

**Issue:** Photostrip composition exceeds Vercel's 60-second limit

**Solutions:**
- Optimize image sizes (capture at lower resolution)
- Switch to Railway/Render for long-running processes
- Implement async processing with background jobs

### Camera Access Denied

**Issue:** Browser won't allow camera access

**Solutions:**
- Use HTTPS (Vercel provides this automatically)
- Check browser permissions
- Test in different browsers (Chrome, Safari, Firefox)

---

## Cost Estimate

### Vercel Free Tier (Hobby)

- **100 GB bandwidth/month** - Sufficient for ~1000 photostrips
- **100 GB-hrs serverless execution** - Sufficient for light usage
- **Unlimited deployments**
- **Automatic HTTPS**
- **Global CDN**

### When to Upgrade

Consider upgrading to Pro ($20/month) if:
- More than 1000 users/month
- Need longer serverless function timeouts
- Need team collaboration features

---

## Next Steps

1. **Set up custom domain** in Vercel dashboard
2. **Configure error tracking** (Sentry integration)
3. **Add analytics** (Vercel Analytics)
4. **Implement Supabase storage** for persistent file storage
5. **Add rate limiting** for API endpoints
6. **Set up CI/CD** for automated testing

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User's Browser                          │
│                  (Chrome, Safari, Mobile)                    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                Vercel Edge Network                          │
│              (React App Static Files)                       │
│  - Global CDN                                               │
│  - Automatic HTTPS                                          │
│  - Edge caching                                             │
└────────────────────┬────────────────────────────────────────┘
                     │ API Calls
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           Vercel Serverless Functions (Python)              │
│              FastAPI Backend                                │
│  - /api/v1/auth/login      (PIN validation)                │
│  - /api/v1/frames          (Frame CRUD)                     │
│  - /api/v1/templates       (Template CRUD)                  │
│  - /api/v1/camera          (Photo capture + frame)          │
│  - /api/v1/composition     (Photostrip generation)           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              File System (Vercel Serverless)                 │
│  - /tmp/frames/          (Frame templates)                  │
│  - /tmp/sessions/        (Temporary photos)                 │
│  - /tmp/strips/          (Completed photostrips)            │
│                                                             │
│  Note: Files in /tmp are ephemeral and may be cleared      │
│        between function invocations.                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Monitoring and Logs

### Viewing Logs

1. Go to Vercel Dashboard
2. Select your project
3. Click "Deployments"
4. Click on a deployment to view logs

### Common Logs to Monitor

- **401 Unauthorized** - Failed PIN attempts
- **404 Not Found** - Missing frame files
- **500 Server Error** - Image processing failures
- **Timeout errors** - Composition taking too long

---

## Support

For issues specific to:
- **Vercel Deployment:** [Vercel Docs](https://vercel.com/docs)
- **FastAPI:** [FastAPI Documentation](https://fastapi.tiangolo.com/)
- **React/Vite:** [Vite Guide](https://vitejs.dev/)

---

**Deployment Checklist:**

- [ ] Backend deployed to Vercel
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] PIN hash set
- [ ] CORS configured
- [ ] Camera access working
- [ ] Photo capture tested
- [ ] Photostrip composition tested
- [ ] Download functionality tested
- [ ] Custom domain configured (optional)
