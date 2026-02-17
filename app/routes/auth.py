from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db

from app.models.user import User
from app.services.cognito_service import CognitoService
from app.exceptions import ServiceException

# Schemas
from app.schemas.user_create import UserCreate
from app.schemas.register_response import RegisterResponse
from app.schemas.user_login import UserLogin 
from app.schemas.login_response import LoginResponse
from app.schemas.user_out import UserOut
from app.schemas.forgot_password import ForgotPasswordRequest


router = APIRouter()
cognito_service = CognitoService

@router.post("/registration", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED,)

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
            "user_confirmed": response.get("UserConfirmed", False)
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")

    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

@router.post("/login", response_model=LoginResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):

    email = payload.email.strip().lower()

    try:
        tokens = cognito_service.authenticate_user(username=email, password=payload.password)

    except ServiceException as e:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in database")
    
    return {"message": "Login successful", "user": user, "tokens": tokens}

@router.post("/forgot-password")

def forgot_password(payload: ForgotPasswordRequest):

    # Normalize email
    email = payload.email.strip().lower()

    try:
        cognito_service.initiate_forgot_password(username=email)

        return {"message": "If the account exists, a reset code will be send."}

    except ServiceException:
        return {"message": "If the account exists, a reset code has been sent."}

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):

    email = payload.email.strip().lower()

    try:
        cognito_service.confirm_forgot_password(
            username=email,
            confirmation_code=payload.confirmation_code,
            new_password=payload.new_password,
        )

        return {"message": "Password reset successful"}

    except ServiceException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
