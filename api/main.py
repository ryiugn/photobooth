"""
FastAPI Backend for Web Photobooth Application

This is a Vercel serverless function that handles:
- Authentication (PIN validation)
- Frame management
- Template CRUD operations
- Photo capture with frame composition
- Photostrip generation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Create FastAPI app
app = FastAPI(
    title="Photobooth API",
    description="Web photobooth backend with frame composition and template management",
    version="1.0.0"
)

# CORS configuration for Vercel deployment
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server
    os.getenv("FRONTEND_URL", "https://your-domain.vercel.app"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Vercel."""
    return {"status": "healthy", "service": "photobooth-api"}

# Import and include routers
from routes import auth, frames, templates, camera, composition

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(frames.router, prefix="/api/v1/frames", tags=["Frames"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(camera.router, prefix="/api/v1/camera", tags=["Camera"])
app.include_router(composition.router, prefix="/api/v1/composition", tags=["Composition"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Photobooth API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Vercel entry point
# This is required for Vercel to recognize the Python serverless function
from fastapi.responses import JSONResponse

async def handler(request):
    """Vercel serverless function entry point."""
    # This will be called by Vercel's Python runtime
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
