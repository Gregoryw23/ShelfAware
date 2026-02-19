from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user_profile import UserProfile
from app.schemas.user_profile import UserProfileCreate, UserProfileOut, UserProfileUpdate
from app.dependencies.auth import get_current_db_user
from app.models.user import User

router = APIRouter()

# 1. GET: Retrieve Profile
@router.get("/me", response_model=UserProfileOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
):
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.user_id
    ).first()

    # Auto-create if missing
    if not profile:
        display_name = current_user.email.split("@")[0]

        profile = UserProfile(
            user_id=current_user.user_id,
            display_name=display_name
        )

        db.add(profile)
        db.commit()
        db.refresh(profile)

    return profile

#2. PATCH: Update Profile (partial allowed)
@router.patch(
    "/me",
    response_model=UserProfileOut,
    status_code=status.HTTP_200_OK,
    summary="Update my profile",
)
def update_my_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user),
):
    """
    Update the authenticated user's profile.

    Only fields provided in the request will be updated.
    """

    # Find existing profile
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.user_id
    ).first()

    # Auto-create profile if missing (safe fallback)
    if not profile:
        default_display_name = current_user.email.split("@")[0]

        profile = UserProfile(
            user_id=current_user.user_id,
            display_name=default_display_name
        )

        db.add(profile)
        db.flush()

    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile