"""Template management routes with user ownership."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import select, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.base import get_db
from models.template import Template
from models.user import User
from routes.users import get_current_user
from lib.logger import log_activity
from datetime import datetime
import json
import uuid

router = APIRouter()


class TemplateCreateRequest(BaseModel):
    """Request to create a template."""
    name: str
    frames: List[str]


class TemplateResponse(BaseModel):
    """Template information."""
    id: str
    name: str
    frames: List[str]
    is_public: bool
    user_id: str
    user_name: str
    created_at: str


class TemplateListResponse(BaseModel):
    """Response containing list of templates."""
    templates: List[TemplateResponse]


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List templates available to current user."""
    result = await db.execute(
        select(Template, User)
        .join(User, Template.user_id == User.id)
        .where(
            or_(
                Template.user_id == current_user.id,
                Template.is_public == True
            )
        )
        .order_by(Template.created_at.desc())
    )

    templates = []
    for template, user in result:
        templates.append(TemplateResponse(
            id=template.id,
            name=template.name,
            frames=json.loads(template.frames),
            is_public=template.is_public,
            user_id=template.user_id,
            user_name=user.name,
            created_at=template.created_at.isoformat()
        ))

    return TemplateListResponse(templates=templates)


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    request: TemplateCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new template from a frame combination."""
    if len(request.frames) != 4:
        raise HTTPException(status_code=400, detail="Template must have exactly 4 frames")

    template_id = str(uuid.uuid4())

    template = Template(
        id=template_id,
        user_id=current_user.id,
        name=request.name,
        frames=json.dumps(request.frames),
        is_public=False,
        created_at=datetime.utcnow()
    )
    db.add(template)

    try:
        await db.commit()
        await db.refresh(template)
    except Exception:
        await db.rollback()
        raise

    # Log activity
    await log_activity(db, current_user.id, "save_template", {
        "template_id": template_id,
        "template_name": request.name,
        "frames": request.frames
    })

    return TemplateResponse(
        id=template.id,
        name=template.name,
        frames=json.loads(template.frames),
        is_public=template.is_public,
        user_id=template.user_id,
        user_name=current_user.name,
        created_at=template.created_at.isoformat()
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific template by ID."""
    result = await db.execute(
        select(Template, User)
        .join(User, Template.user_id == User.id)
        .where(Template.id == template_id)
    )

    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")

    template, user = row

    # Check access
    if template.user_id != current_user.id and not template.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    return TemplateResponse(
        id=template.id,
        name=template.name,
        frames=json.loads(template.frames),
        is_public=template.is_public,
        user_id=template.user_id,
        user_name=user.name,
        created_at=template.created_at.isoformat()
    )


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a template (only owner or admin)."""
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check ownership
    if template.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Not your template")

    # Delete
    await db.delete(template)
    await db.commit()

    # Log activity
    await log_activity(db, current_user.id, "delete_template", {
        "template_id": template_id,
        "template_name": template.name
    })

    return {"message": "Template deleted successfully"}


@router.patch("/{template_id}/public")
async def toggle_template_public(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle template public visibility."""
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check ownership
    if template.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your template")

    # Toggle
    template.is_public = not template.is_public
    await db.commit()

    return {"is_public": template.is_public}
