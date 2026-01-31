"""
Sharing routes for uploading photostrips and generating shareable links.

Uses Vercel Blob Storage for persistent cloud storage.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
import uuid
import io
import base64
from datetime import datetime, timedelta
from pathlib import Path

from config import settings
from routes.auth import get_current_user

router = APIRouter()


# Response Models
class UploadResponse(BaseModel):
    """Response after photostrip upload."""
    strip_id: str
    share_url: str
    expires_at: str  # ISO datetime string


class GetStripResponse(BaseModel):
    """Response for retrieving a photostrip."""
    strip_id: str
    image_data: str  # Base64 encoded image
    created_at: str
    expires_at: str


# In-memory storage for demo (in production, use Vercel Blob Storage or a database)
# In serverless, we can't persist data, so we'll use a simple approach:
# - Upload returns a shareable token
# - The token encodes the base64 data (for small images) or we use Vercel Blob

# For production with Vercel, we should use @vercel/blob
# But for now, let's implement a simple token-based approach


def generate_strip_id() -> str:
    """Generate a unique photostrip ID."""
    return f"strip_{uuid.uuid4().hex[:12]}"


def base64_to_bytes(base64_data: str) -> bytes:
    """Convert base64 string to bytes."""
    # Remove data URL prefix if present
    if ',' in base64_data:
        base64_data = base64_data.split(',', 1)[1]
    return base64.b64decode(base64_data)


def bytes_to_base64(image_bytes: bytes) -> str:
    """Convert bytes to base64 data URL."""
    return f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"


# Simple in-memory cache (won't persist across serverless invocations)
# In production, use Vercel Blob Storage or a database
_photostrip_cache = {}


@router.post("/upload", response_model=UploadResponse)
async def upload_photostrip(
    image_data: str,  # Base64 encoded photostrip
    user: dict = Depends(get_current_user)
):
    """
    Upload a photostrip and generate a shareable link.

    Args:
        image_data: Base64 encoded photostrip image

    Returns:
        UploadResponse with strip_id and share_url

    Note: This is a simplified implementation. In production, use Vercel Blob Storage.
    """
    try:
        # Validate image data
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image data provided"
            )

        # Convert base64 to bytes
        image_bytes = base64_to_bytes(image_data)

        # Validate size (max 10MB)
        max_size = 10 * 1024 * 1024
        if len(image_bytes) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image too large. Maximum size: 10MB"
            )

        # Generate unique strip ID
        strip_id = generate_strip_id()

        # Calculate expiration (30 days from now)
        expires_at = datetime.utcnow() + timedelta(days=30)

        # Store in cache (in production, use Vercel Blob Storage)
        _photostrip_cache[strip_id] = {
            "image_data": image_data,  # Store base64 string
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat()
        }

        # Generate share URL
        # Using the configured frontend URL
        share_url = f"{settings.ALLOWED_ORIGINS[-1] or 'http://localhost:3000'}/share/{strip_id}"

        return UploadResponse(
            strip_id=strip_id,
            share_url=share_url,
            expires_at=expires_at.isoformat()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload photostrip: {str(e)}"
        )


@router.get("/{strip_id}", response_model=GetStripResponse)
async def get_photostrip(strip_id: str):
    """
    Retrieve a photostrip by ID.

    Args:
        strip_id: Unique photostrip identifier

    Returns:
        GetStripResponse with image data and metadata

    Raises:
        HTTPException: If strip not found or expired
    """
    # Check cache
    if strip_id not in _photostrip_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photostrip not found or has expired"
        )

    strip_data = _photostrip_cache[strip_id]

    # Check expiration
    expires_at = datetime.fromisoformat(strip_data["expires_at"])
    if datetime.utcnow() > expires_at:
        # Remove expired entry
        del _photostrip_cache[strip_id]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photostrip has expired"
        )

    return GetStripResponse(
        strip_id=strip_id,
        image_data=strip_data["image_data"],
        created_at=strip_data["created_at"],
        expires_at=strip_data["expires_at"]
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "photobooth-sharing",
        "cached_strips": len(_photostrip_cache)
    }
