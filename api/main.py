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

# Import settings
from config import settings

# Create FastAPI app
app = FastAPI(
    title="Photobooth API",
    description="Web photobooth backend with frame composition and template management",
    version="1.0.0"
)

# CORS configuration for Vercel deployment
# Add production web deployment URLs to allowed origins
PRODUCTION_WEB_URLS = [
    "https://ryiugn-photobooth.vercel.app",
    "https://web-ryiugns-projects.vercel.app",
    "https://web-909ax5xr8-ryiugns-projects.vercel.app",
    "https://web-8zunao3z5-ryiugns-projects.vercel.app",
    "https://web-sandy-xi-35.vercel.app",
]

# Combine local origins with settings and production URLs
ALLOWED_ORIGINS = list(settings.ALLOWED_ORIGINS)  # Start with config settings
for url in PRODUCTION_WEB_URLS:
    if url not in ALLOWED_ORIGINS:
        ALLOWED_ORIGINS.append(url)

# Log CORS configuration for debugging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"CORS ALLOWED_ORIGINS: {ALLOWED_ORIGINS}")

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

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Photobooth API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Import and include routers
from routes import auth, frames, templates, camera, composition, sharing

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(frames.router, prefix="/api/v1/frames", tags=["Frames"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(camera.router, prefix="/api/v1/camera", tags=["Camera"])
app.include_router(composition.router, prefix="/api/v1/composition", tags=["Composition"])
app.include_router(sharing.router, prefix="/api/v1/sharing", tags=["Sharing"])


# Vercel serverless entry point
# Export the ASGI app for Vercel
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
