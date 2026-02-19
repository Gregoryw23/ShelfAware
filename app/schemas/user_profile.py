from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

# Base model with rich examples for Swagger UI
class UserProfileBase(BaseModel):
    display_name: str = Field(
        ...,
        title="Display Name",
        description="The public name shown to other users.",
        examples=["BookLover99"]
    )
    profile_photo_url: Optional[str] = Field(
        None,
        title="Avatar URL",
        description="URL link to the user's profile picture.",
        examples=["https://example.com/images/avatar_001.jpg"]
    )
    bio: Optional[str] = Field(
        None,
        title="Biography",
        description="A short introduction about reading preferences.",
        examples=["Sci-Fi enthusiast. Currently reading 'Dune'."]
    )
    location: Optional[str] = Field(
        None,
        title="Location",
        description="The city or region where the user resides.",
        examples=["New York, USA"]
    )
    favorite_genres_json: Optional[str] = Field(
        None,
        title="Favorite Genres",
        description="JSON string representing a list of favorite genres.",
        examples=['["Science Fiction", "Mystery", "History"]']
    )

# Patch model for updates
class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    profile_photo_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    favorite_genres_json: Optional[str] = None

# POST request model
class UserProfileCreate(UserProfileBase):
    pass

# Response model for the owner (includes user_id)
class UserProfileOut(UserProfileBase):
    user_id: str
    model_config = ConfigDict(from_attributes=True)

# --- NEW: Response model for public view (Hides user_id) ---
class UserProfilePublic(BaseModel):
    display_name: str
    profile_photo_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    favorite_genres_json: Optional[str] = None

    # New calculated fields for Greg's requirements
    profile_completeness: int  # Percentage (0-100)
    member_since: str         # Formatted date string (e.g., "February 2026")

    model_config = ConfigDict(from_attributes=True)