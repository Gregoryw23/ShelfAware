from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db

from datetime import datetime, timedelta,timezone

# Models
from app.models.user import User

from app.services.cognito_service import CognitoService

# Schemas
from app.schemas.user_create import UserCreate
from app.schemas.register_response import RegisterResponse
from app.schemas.user_out import UserOut
from app.schemas.user_login import UserLogin 
from app.schemas.forgot_password import ForgotPasswordRequest


router = APIRouter()
cognito_service = cognito_service

@router.post("/registration", response_model=UserOut, status_code=status.HTTP_201_CREATED,)

def register(payload: UserCreate, db: Session = Depends(get_db)):
    
    # Normalize email
    email = payload.email.strip().lower()
    
    # Check if email already exists locally
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        response = cognito_service.register_user(
        username=email,
        email=email,
        password=payload.password
    )

    # Create new user in DB
    new_user = User(
        email=email,
        cognito_sub=response["UserSub"]
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "User registration successful.",
        "user_sub": new_user,
        "user_confirmed": response["UserConfirmed"]
        }

    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

@router.post("/forgot-password")

def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):

    # Normalize email
    email = payload.email.strip().lower()

    # Check if email already exists
    user = db.query(User).filter(User.email == email).first()

    # Always return same response (security best practice)
    if not user:
        return {"message": "If the email exists, a reset link will be sent."}

    token = secrets.token_urlsafe(32)

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).replace(tzinfo=None)

    reset_token = PasswordResetToken(
        token=token,
        user_id=user.user_id,
        expires_at=expires_at,
    )

    db.add(reset_token)
    db.commit()

    # TEMP: print token for testing
    print(f"[RESET TOKEN] email={email} token={token}")

    return {"message": "If the email exists, a reset link will be sent."}

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):

    token = payload.token
    new_password = payload.new_password

    reset_record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == token)
        .first()
    )

    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid token")

    if reset_record.used:
        raise HTTPException(status_code=400, detail="Token already used")
    
    now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    if reset_record.expires_at < now_utc_naive:
        raise HTTPException(status_code=400, detail="Token expired")

    user = db.query(User).filter(User.user_id == reset_record.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # hash new password
    user.password_hash = hash_password(new_password)

    # mark token used
    reset_record.used = True

    db.commit()

    return {"message": "Password reset successful"}

@router.post("/login", response_model=UserOut)
def login(payload: UserLogin, db: Session = Depends(get_db)):

    email = payload.email.strip().lower()

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return user
