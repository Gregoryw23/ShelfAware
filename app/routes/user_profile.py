from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.models.user_profile import UserProfile
from app.models.user import User
from app.dependencies.auth import get_current_db_user
from app.schemas.user_profile import (
    UserProfileCreate,
    UserProfileOut,
    UserProfileUpdate,
    UserProfilePublic  # Added this import
)

# Crucial: Define router instance for app/main.py
router = APIRouter()

# 1. GET: Retrieve Authenticated User's Profile
@router.get("/me", response_model=UserProfileOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
):
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.user_id
    ).first()

    if not profile:
        display_name = current_user.email.split("@")[0]
        profile = UserProfile(user_id=current_user.user_id, display_name=display_name)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return profile

# 2. PATCH: Update Authenticated User's Profile
@router.patch("/me", response_model=UserProfileOut)
def update_my_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
):
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.user_id
    ).first()

    if not profile:
        profile = UserProfile(
            user_id=current_user.user_id,
            display_name=current_user.email.split("@")[0]
        )
        db.add(profile)
        db.flush()

    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile

# --- 3. GET: Public Profile View by Username (Read-Only) ---
@router.get(
    "/public/{display_name}",
    response_model=UserProfilePublic,
    summary="View someone's public profile with statistics"
)
def get_public_profile_by_name(display_name: str, db: Session = Depends(get_db)):
    # 1. Fetch profile by display name
    profile = db.query(UserProfile).filter(
        UserProfile.display_name == display_name
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Fetch associated user to get account creation date
    user = db.query(User).filter(User.user_id == profile.user_id).first()

    # Logic: Calculate Profile Completeness Score
    # We check 4 key fields: bio, location, photo, and genres
    tracked_fields = [
        profile.bio,
        profile.location,
        profile.profile_photo_url,
        profile.favorite_genres_json
    ]
    filled_count = len([f for f in tracked_fields if f and str(f).strip() != ""])
    completeness = int((filled_count / len(tracked_fields)) * 100)

    # Logic: Format "Member Since" string
    member_since_str = user.created_at.strftime("%B %Y") if user and user.created_at else "Unknown"

    return {
        "display_name": profile.display_name,
        "profile_photo_url": profile.profile_photo_url,
        "bio": profile.bio,
        "location": profile.location,
        "favorite_genres_json": profile.favorite_genres_json,
        "profile_completeness": completeness,
        "member_since": member_since_str
    }