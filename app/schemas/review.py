from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    comment: str
    mood: Optional[str] = Field(None, description="Optional user mood as free text")

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    mood: Optional[str] = None

class ReviewOut(ReviewBase):
    id: UUID
    book_id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)
