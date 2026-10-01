"""Authentication API routes for EviBite AI.

Provides user registration, sign in, and profile token verification.
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from backend.app.db.user_repository import user_repo

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=60, description="User full name")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    plan_tier: str = "free"
    daily_msg_count: int = 0
    created_at: Optional[str] = None


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class PlanUpdateRequest(BaseModel):
    user_id: str = Field(..., description="User ID to update")
    plan_tier: str = Field(..., description="Target plan tier: free, pro, ultimate")


@router.post("/register", response_model=AuthResponse)
def register_user(req: RegisterRequest):
    """Register a new user in MongoDB and return JWT token."""
    email_clean = req.email.lower().strip()
    if user_repo.find_by_email(email_clean):
        raise HTTPException(
            status_code=400,
            detail="An account with this email address already exists. Please sign in.",
        )

    try:
        user_info = user_repo.create_user(
            name=req.name,
            email=email_clean,
            password=req.password,
        )
        token = user_repo.create_token(
            user_id=user_info["id"],
            email=user_info["email"],
            name=user_info["name"],
        )
        return AuthResponse(
            token=token,
            user=UserResponse(**user_info),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=AuthResponse)
def login_user(req: LoginRequest):
    """Sign in an existing user with email and password."""
    email_clean = req.email.lower().strip()
    user = user_repo.find_by_email(email_clean)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password. Please check your credentials.",
        )

    if not user_repo.verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password. Please check your credentials.",
        )

    token = user_repo.create_token(
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
    )
    user_info = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "plan_tier": user.get("plan_tier", "free"),
        "daily_msg_count": user.get("daily_msg_count", 0),
        "created_at": user.get("created_at"),
    }
    return AuthResponse(
        token=token,
        user=UserResponse(**user_info),
    )


@router.get("/me", response_model=UserResponse)
def get_current_user(authorization: Optional[str] = Header(None)):
    """Verify authorization token and return logged-in user profile."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization token.",
        )

    token = authorization.split("Bearer ")[1].strip()
    payload = user_repo.decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token has expired or is invalid. Please sign in again.",
        )

    user = user_repo.find_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        plan_tier=user.get("plan_tier", "free"),
        daily_msg_count=user.get("daily_msg_count", 0),
        created_at=user.get("created_at"),
    )


@router.post("/update-plan", response_model=UserResponse)
def update_user_plan(req: PlanUpdateRequest):
    """Update subscription plan tier for a user."""
    try:
        updated_user = user_repo.update_user_tier(req.user_id, req.plan_tier)
        return UserResponse(
            id=updated_user.get("id", req.user_id),
            name=updated_user.get("name", "User"),
            email=updated_user.get("email", ""),
            plan_tier=updated_user.get("plan_tier", req.plan_tier),
            daily_msg_count=updated_user.get("daily_msg_count", 0),
            created_at=updated_user.get("created_at"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
