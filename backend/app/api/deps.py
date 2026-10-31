from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User
from app.core.security import decode_access_token
from app.services.supabase_service import SupabaseService

security_scheme = HTTPBearer(auto_error=False)

def _get_user_from_token(token: str, db: Session) -> Optional[User]:
    if not token:
        return None

    # 1. If Supabase is configured, attempt Supabase token verification
    if SupabaseService.is_configured():
        sb_user = SupabaseService.verify_token(token)
        if sb_user:
            sb_id = sb_user["id"]
            user = db.query(User).filter(User.supabase_id == sb_id).first()
            if not user:
                # Also check by email to link account
                user = db.query(User).filter(User.email == sb_user["email"].lower()).first()
                if user:
                    user.supabase_id = sb_id
                    db.commit()
                else:
                    # Create local mirror user
                    user = User(
                        supabase_id=sb_id,
                        email=sb_user["email"].lower(),
                        full_name=sb_user["full_name"],
                        hashed_password=""
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
            return user

    # 2. Local JWT token verification
    payload = decode_access_token(token)
    if payload and "sub" in payload:
        sub_val = payload["sub"]
        try:
            user = db.query(User).filter(User.id == int(sub_val)).first()
            if user:
                return user
        except (ValueError, TypeError):
            # Check by supabase_id if sub is a string UUID
            user = db.query(User).filter(User.supabase_id == str(sub_val)).first()
            if user:
                return user
    return None

def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    token = None
    if creds:
        token = creds.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = _get_user_from_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def get_optional_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    token = None
    if creds:
        token = creds.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")
    
    if not token:
        return None

    return _get_user_from_token(token, db)
