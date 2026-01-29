"""User registration and authentication endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, UserRole
from models.base import get_db
import bcrypt
import httpx
from itsdangerous import URLSafeSerializer
from config import settings

router = APIRouter()
security = HTTPBearer()

# OAuth state storage (in production, use Redis)
oauth_states = {}


# Request/Response Models
class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    name: str = Field(min_length=1, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class LoginRequest(BaseModel):
    """Email/password login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User information response."""
    id: str
    email: str
    name: str
    role: str


class AuthResponse(BaseModel):
    """Authentication response with token."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GoogleAuthURLResponse(BaseModel):
    """Google OAuth URL response."""
    auth_url: str
    state: str


class GoogleCallbackRequest(BaseModel):
    """Google OAuth callback request."""
    code: str
    state: str


# Utility Functions
def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(data: dict) -> str:
    """Create JWT access token."""
    from jose import jwt
    from datetime import datetime, timedelta
    from config import settings

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)) -> User:
    """Get current user from JWT token."""
    from jose import jwt, JWTError
    from config import settings

    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_google_config() -> dict:
    """Get Google OAuth configuration."""
    return {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo"
    }


def generate_state() -> str:
    """Generate OAuth state token."""
    import secrets
    import time
    state_data = {"nonce": secrets.token_urlsafe(32), "timestamp": time.time()}
    serializer = URLSafeSerializer(settings.JWT_SECRET, "oauth")
    state = serializer.dumps(state_data)
    oauth_states[state] = state_data
    return state


def verify_state(state: str) -> bool:
    """Verify OAuth state token."""
    if state not in oauth_states:
        return False
    # Remove used state
    del oauth_states[state]
    return True


# Routes
@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check if email exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if this is the first user (becomes admin)
    result = await db.execute(select(func.count(User.id)))
    user_count = result.scalar() or 0
    role = UserRole.ADMIN if user_count == 0 else UserRole.USER

    # Create user
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        name=request.name,
        role=role
    )
    db.add(user)

    try:
        await db.commit()
        await db.refresh(user)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )

    # Create token
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role
    })

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role
        )
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    # Find user
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create token
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role
    })

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role
    )


@router.get("/google/url", response_model=GoogleAuthURLResponse)
async def get_google_auth_url():
    """Get Google OAuth authorization URL."""
    config = get_google_config()
    state = generate_state()

    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": "openid email profile",
        "state": state
    }

    from urllib.parse import urlencode
    auth_url = f"{config['auth_url']}?{urlencode(params)}"

    return GoogleAuthURLResponse(auth_url=auth_url, state=state)


@router.post("/google/callback", response_model=AuthResponse)
async def google_callback(request: GoogleCallbackRequest, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback."""
    # Verify state
    if not verify_state(request.state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )

    config = get_google_config()

    # Exchange code for tokens
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            token_response = await client.post(
                config["token_url"],
                data={
                    "code": request.code,
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "redirect_uri": config["redirect_uri"],
                    "grant_type": "authorization_code"
                }
            )
            token_data = token_response.json()

            if "error" in token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=token_data.get("error_description", "OAuth failed")
                )

            # Get user info
            user_response = await client.get(
                config["user_info_url"],
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            user_info = user_response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to connect to Google"
            ) from e

    # Verify email is verified
    if not user_info.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )

    # Find or create user
    result = await db.execute(
        select(User).where(User.google_id == user_info["id"])
    )
    user = result.scalar_one_or_none()

    if not user:
        # Check if email already exists
        result = await db.execute(
            select(User).where(User.email == user_info["email"])
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Link Google account to existing user
            existing_user.google_id = user_info["id"]
            user = existing_user
        else:
            # Check if this is the first user
            result = await db.execute(select(func.count(User.id)))
            user_count = result.scalar() or 0
            role = UserRole.ADMIN if user_count == 0 else UserRole.USER

            # Create new user
            user = User(
                email=user_info["email"],
                google_id=user_info["id"],
                name=user_info.get("name", user_info["email"].split("@")[0]),
                role=role
            )
            db.add(user)

        try:
            await db.commit()
            await db.refresh(user)
        except Exception:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )

    # Create token
    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role
    })

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role
        )
    )
