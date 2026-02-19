from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


# Base model with rich examples for Swagger UI "Try it out" autofill
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


# POST request model (Defines the input box structure)
class UserProfileCreate(UserProfileBase):
    pass


# Response model (Includes user_id in the output)
class UserProfileOut(UserProfileBase):
    user_id: str

    model_config = ConfigDict(from_attributes=True)