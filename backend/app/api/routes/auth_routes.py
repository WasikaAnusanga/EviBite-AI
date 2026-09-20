import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field

from backend.app.db.database import get_db
from backend.app.security.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignUpRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=6, max_length=100)


class SignInRequest(BaseModel):
    email: str
    password: str



class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/signup", response_model=AuthResponse)
def signup(request: SignUpRequest):
    db = get_db()
    
    # Check if user with email already exists
    existing = db.users.find_one({"email": request.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(request.password)
    now_iso = datetime.now(timezone.utc).isoformat()

    user_doc = {
        "_id": user_id,
        "full_name": request.full_name,
        "email": request.email.lower(),
        "hashed_password": hashed_pwd,
        "created_at": now_iso,
    }

    db.users.insert_one(user_doc)

    token = create_access_token({"sub": user_id, "email": request.email.lower()})

    user_info = {
        "id": user_id,
        "full_name": request.full_name,
        "email": request.email.lower(),
        "created_at": now_iso,
    }

    return AuthResponse(access_token=token, user=user_info)


@router.post("/signin", response_model=AuthResponse)
def signin(request: SignInRequest):
    db = get_db()
    user = db.users.find_one({"email": request.email.lower()})

    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token({"sub": str(user["_id"]), "email": user["email"]})

    user_info = {
        "id": str(user["_id"]),
        "full_name": user["full_name"],
        "email": user["email"],
        "created_at": user.get("created_at"),
    }

    return AuthResponse(access_token=token, user=user_info)


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "created_at": current_user.get("created_at"),
    }
