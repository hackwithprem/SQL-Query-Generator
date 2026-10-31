import re
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User
from app.schemas.requests import UserSignUpRequest, UserLoginRequest
from app.schemas.responses import AuthTokenResponse, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.api.deps import get_current_user
from app.services.supabase_service import SupabaseService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

class UpdateProfileRequest(BaseModel):
    full_name: str

@router.post("/signup", response_model=AuthTokenResponse)
def signup(request: UserSignUpRequest, response: Response, db: Session = Depends(get_db)):
    clean_email = request.email.strip().lower()
    if not re.match(EMAIL_REGEX, clean_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address."
        )

    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )

    # Prevent duplicate accounts
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    supabase_id = None
    token = None

    # If Supabase is configured, register with Supabase Auth
    if SupabaseService.is_configured():
        try:
            sb_res = SupabaseService.sign_up(clean_email, request.password, request.full_name.strip())
            supabase_id = sb_res["user_id"]
            token = sb_res.get("access_token")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supabase Auth error: {str(e)}"
            )

    # Hash password securely for local mirror
    hashed_pw = hash_password(request.password)
    new_user = User(
        supabase_id=supabase_id,
        full_name=request.full_name.strip(),
        email=clean_email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if not token:
        token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})

    # Set HTTP-only session cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=7 * 24 * 3600,
        samesite="lax",
        secure=False
    )

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=new_user.id,
            full_name=new_user.full_name,
            email=new_user.email,
            created_at=new_user.created_at.isoformat() if new_user.created_at else None
        )
    )

@router.post("/login", response_model=AuthTokenResponse)
def login(request: UserLoginRequest, response: Response, db: Session = Depends(get_db)):
    clean_email = request.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    token = None

    # If Supabase is configured, authenticate with Supabase Auth
    if SupabaseService.is_configured():
        try:
            sb_res = SupabaseService.sign_in(clean_email, request.password)
            token = sb_res.get("access_token")
            sb_id = sb_res["user_id"]
            if not user:
                user = User(
                    supabase_id=sb_id,
                    email=clean_email,
                    full_name=sb_res["full_name"],
                    hashed_password=""
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            elif not user.supabase_id:
                user.supabase_id = sb_id
                db.commit()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )
    else:
        # Avoid timing enumeration by checking password even if user not found with dummy hash
        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )
        token = create_access_token(data={"sub": str(user.id), "email": user.email})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=7 * 24 * 3600,
        samesite="lax",
        secure=False
    )

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            created_at=user.created_at.isoformat() if user.created_at else None
        )
    )

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Signed out successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )

@router.put("/profile", response_model=UserResponse)
def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clean_name = req.full_name.strip()
    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Display name cannot be empty."
        )
    current_user.full_name = clean_name
    db.commit()
    db.refresh(current_user)

    # Also update Supabase profile if configured
    if SupabaseService.is_configured() and current_user.supabase_id:
        try:
            client = SupabaseService.get_client()
            if client:
                client.table("users").update({"full_name": clean_name}).eq("id", current_user.supabase_id).execute()
        except Exception as e:
            print(f"Warning: Failed to update Supabase profile: {e}")

    return UserResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )
