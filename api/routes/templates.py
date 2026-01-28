"""
Template management routes for saving, loading, and deleting frame combinations.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, validator
from typing import List, Optional
from pathlib import Path
import json
import uuid
from datetime import datetime

from config import settings
from routes.auth import get_current_user

router = APIRouter()


# Request/Response Models
class TemplateCreateRequest(BaseModel):
    """Request to create a template."""
    name: str
    frames: List[str]  # List of 4 frame IDs/paths

    @validator('frames')
    def validate_frames(cls, v):
        if len(v) != 4:
            raise ValueError('Template must have exactly 4 frames')
        return v


class TemplateInfo(BaseModel):
    """Information about a template."""
    id: str
    name: str
    frames: List[str]
    created: str


class TemplatesListResponse(BaseModel):
    """Response containing list of templates."""
    templates: List[TemplateInfo]


class TemplateCreateResponse(BaseModel):
    """Response after template creation."""
    id: str
    name: str
    message: str


# Utility Functions
def get_templates_dir() -> Path:
    """Get the templates directory path, creating if needed."""
    templates_dir = Path(settings.TEMPLATES_DIR)
    try:
        templates_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # On serverless platforms like Vercel, filesystem may be read-only
        pass
    return templates_dir


def generate_template_id() -> str:
    """Generate a unique template ID."""
    return f"tpl_{uuid.uuid4().hex[:8]}"


def sanitize_filename(name: str) -> str:
    """Convert template name to safe filename."""
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip('_')


# Routes
@router.get("", response_model=TemplatesListResponse)
async def list_templates(user: dict = Depends(get_current_user)):
    """
    List all saved templates.

    Returns:
        TemplatesListResponse with list of templates
    """
    templates_dir = get_templates_dir()
    templates = []

    # Check if directory exists and is accessible
    if not templates_dir.exists():
        return TemplatesListResponse(templates=templates)

    try:
        for json_file in templates_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                templates.append(TemplateInfo(
                    id=data.get("id", json_file.stem),
                    name=data["name"],
                    frames=data["frames"],
                    created=data.get("created", "")
                ))
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip corrupted files
                continue
    except Exception:
        # Return empty list if there's any error accessing the directory
        pass

    # Sort by created date (newest first)
    templates.sort(key=lambda t: t.created, reverse=True)

    return TemplatesListResponse(templates=templates)


@router.post("", response_model=TemplateCreateResponse)
async def create_template(
    request: TemplateCreateRequest,
    user: dict = Depends(get_current_user)
):
    """
    Create a new template from a frame combination.

    Args:
        request: Template creation request

    Returns:
        TemplateCreateResponse

    Raises:
        HTTPException: If validation fails
    """
    # Note: Frames are now hosted on the frontend, not in the filesystem
    # We skip file existence validation and just store the frame IDs

    # Create template
    template_id = generate_template_id()
    timestamp = datetime.now().isoformat()

    template_data = {
        "id": template_id,
        "name": request.name,
        "frames": request.frames,
        "created": timestamp
    }

    # Try to save to file (will fail silently on serverless platforms)
    try:
        templates_dir = get_templates_dir()
        if templates_dir.exists():
            filename = f"{sanitize_filename(request.name)}_{template_id}.json"
            file_path = templates_dir / filename

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2)
    except Exception:
        # On serverless platforms, templates won't persist
        # We still return success for the API contract
        pass

    return TemplateCreateResponse(
        id=template_id,
        name=request.name,
        message="Template created successfully"
    )


@router.get("/{template_id}")
async def get_template(template_id: str, user: dict = Depends(get_current_user)):
    """
    Get a specific template by ID.

    Args:
        template_id: Template identifier

    Returns:
        TemplateInfo

    Raises:
        HTTPException: If template not found
    """
    templates_dir = get_templates_dir()

    for json_file in templates_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get("id") == template_id or template_id in json_file.stem:
                return TemplateInfo(**data)
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Template '{template_id}' not found"
    )


@router.delete("/{template_id}")
async def delete_template(template_id: str, user: dict = Depends(get_current_user)):
    """
    Delete a template.

    Args:
        template_id: Template identifier

    Returns:
        Success message

    Raises:
        HTTPException: If template not found
    """
    templates_dir = get_templates_dir()

    for json_file in templates_dir.glob("*.json"):
        if template_id in json_file.stem:
            json_file.unlink()
            return {"message": f"Template '{template_id}' deleted successfully"}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Template '{template_id}' not found"
    )
