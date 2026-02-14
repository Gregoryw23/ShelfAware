from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.models.user import User
from app.schemas.user_create import UserCreate
from app.schemas.user_out import UserOut
from app.core.security import hash_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
        "/register",
        response_model=UserOut,
        status_code=status.HTTP_201_CREATED,
        )

def register(payload: UserCreate, db: Session = Depends(get_db)):
    
    # Normalize email
    email = payload.email.strip().lower()

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Hash password
    hashed_pw = hash_password(payload.password)

    # Create new user
    new_user = User(
        email=email,
        password_hash=hashed_pw
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return new_user