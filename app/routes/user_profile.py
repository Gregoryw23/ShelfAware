from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user_profile import UserProfile
from app.schemas.user_profile import UserProfileCreate, UserProfileOut

router = APIRouter(
    prefix="/user_profile",
    tags=["UserProfile"]
)

# Hardcoded User ID for development (Default)
TEST_USER_ID = "test-user-id-001"


# --- Define Enums for Delete Options ---
# This creates a Dropdown menu in Swagger UI
class DeletableField(str, Enum):
    bio = "bio"
    location = "location"
    profile_photo_url = "profile_photo_url"
    favorite_genres_json = "favorite_genres_json"
    display_name = "display_name"
    # Select 'ALL_PROFILE' to delete the entire record
    ALL_PROFILE = "ALL_PROFILE"


# ==========================================
# 1. POST: Create or Update (Upsert)
# ==========================================
@router.post("/", response_model=UserProfileOut, status_code=status.HTTP_200_OK, summary="Create or Update Profile")
def create_or_update_profile(
        profile_data: UserProfileCreate,
        db: Session = Depends(get_db)
):
    """
    **Create or Update the user profile.**
    """
    user_id = TEST_USER_ID

    db_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if db_profile:
        # Update existing
        update_data = profile_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_profile, key, value)
    else:
        # Create new
        db_profile = UserProfile(user_id=user_id, **profile_data.model_dump())
        db.add(db_profile)

    db.commit()
    db.refresh(db_profile)
    return db_profile


# ==========================================
# 2. GET: Retrieve Profile (With Input)
# ==========================================
@router.get("/", response_model=UserProfileOut, summary="Get Profile")
def get_my_profile(
        target_user_id: Optional[str] = Query(
            None,
            description="Input a specific User ID to fetch. If empty, uses default test user.",
            examples=["test-user-id-001"]
        ),
        db: Session = Depends(get_db)
):
    """
    **Retrieve a user profile.**

    - **Input**: You can now input a `target_user_id` in the box below.
    - If you leave it empty, it defaults to the test user.
    """
    # Use input ID if provided, otherwise use default
    user_id = target_user_id if target_user_id else TEST_USER_ID

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile not found for user_id: {user_id}")

    return profile


# ==========================================
# 3. DELETE: Remove Specific Field or All
# ==========================================
@router.delete("/", status_code=status.HTTP_200_OK, summary="Delete Field or Profile")
def delete_profile_field(
        field_to_delete: Optional[DeletableField] = Query(
            None,
            description="Select which part of the profile to delete. Select 'ALL_PROFILE' to remove everything."
        ),
        db: Session = Depends(get_db)
):
    """
    **Flexible Delete Operation.**

    - **Pick a field**: e.g., select `bio` to clear only the bio (set to null).
    - **ALL_PROFILE**: Deletes the entire user record from the database.
    - **Empty**: If you don't select anything, it does nothing (safety check).
    """
    user_id = TEST_USER_ID
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # 1. Safety Check: If user didn't select anything
    if not field_to_delete:
        return {"message": "No field selected. Nothing was deleted."}

    # 2. Delete Entire Profile
    if field_to_delete == DeletableField.ALL_PROFILE:
        db.delete(profile)
        db.commit()
        return {"message": "Entire profile has been deleted."}

    # 3. Delete Specific Column (Set to None/Null)
    # We use setattr to dynamically access the column name
    # e.g., setattr(profile, "bio", None)

    # Check if the field is nullable (display_name usually isn't)
    if field_to_delete == DeletableField.display_name:
        raise HTTPException(status_code=400, detail="Display Name cannot be deleted (it is required).")

    setattr(profile, field_to_delete.value, None)

    db.commit()
    db.refresh(profile)

    return {
        "message": f"Successfully deleted (cleared) field: {field_to_delete.value}",
        "current_profile": {
            "user_id": profile.user_id,
            "bio": profile.bio,
            "location": profile.location,
            "profile_photo_url": profile.profile_photo_url
        }
    }