"""
Authentication routes for PIN-based login and session management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt

from config import settings
from models.base import get_db
from models.user import User, UserRole

router = APIRouter()
security = HTTPBearer()


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request model."""
    pin: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class VerifyResponse(BaseModel):
    """Token verification response."""
    valid: bool
    session_id: Optional[str] = None


# Utility Functions
def verify_pin(pin: str) -> bool:
    """Verify the entered PIN against the hashed PIN."""
    try:
        # Convert hashed PIN from string to bytes
        pin_hash_bytes = settings.PIN_HASH.encode('utf-8') if isinstance(settings.PIN_HASH, str) else settings.PIN_HASH
        pin_bytes = pin.encode('utf-8')
        return bcrypt.checkpw(pin_bytes, pin_hash_bytes)
    except Exception as e:
        print(f"PIN verification error: {e}")
        return False


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Routes
@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user with PIN and return JWT token.

    For PIN authentication, creates/uses a guest user account.

    Args:
        request: Login request with PIN
        db: Database session

    Returns:
        LoginResponse with access token

    Raises:
        HTTPException: If PIN is invalid
    """
    # Validate PIN format (4-6 digits)
    if not request.pin.isdigit() or len(request.pin) < 4 or len(request.pin) > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PIN must be 4-6 digits"
        )

    # Verify PIN
    if not verify_pin(request.pin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect PIN"
        )

    # For PIN auth, use a special guest user
    # Create or get the guest user
    guest_email = "guest@photobooth.local"
    result = await db.execute(select(User).where(User.email == guest_email))
    guest_user = result.scalar_one_or_none()

    if not guest_user:
        # Create guest user
        import uuid
        guest_user = User(
            id=str(uuid.uuid4()),
            email=guest_email,
            name="Guest User",
            role=UserRole.USER
        )
        db.add(guest_user)
        await db.commit()
        await db.refresh(guest_user)

    # Create access token with actual user ID
    token_data = {
        "sub": guest_user.id,
        "email": guest_user.email,
        "role": guest_user.role,
        "type": "pin_session"
    }
    access_token = create_access_token(token_data)

    return LoginResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user (invalidate token).

    Note: In a stateless JWT system, logout is handled client-side
    by deleting the token. This endpoint exists for future session tracking.
    """
    # For future implementation with server-side session tracking
    return {"message": "Logged out successfully"}


@router.get("/verify", response_model=VerifyResponse)
async def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify if a JWT token is valid.

    Returns:
        VerifyResponse indicating token validity
    """
    try:
        payload = verify_token(credentials.credentials)
        return VerifyResponse(
            valid=True,
            session_id=payload.get("sub")
        )
    except HTTPException:
        return VerifyResponse(valid=False)


# Dependency for protected routes (returns dict for backward compatibility)
async def get_current_user_dict(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency for routes that require authentication.

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid
    """
    return verify_token(credentials.credentials)


# New dependency that returns User object (for activity logging)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency for routes that require User object.

    Returns:
        User object from database

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token_data = verify_token(credentials.credentials)
    user_id = token_data.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user
