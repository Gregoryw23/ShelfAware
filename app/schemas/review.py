# app/schemas/review.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Union
from datetime import datetime


class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    comment: Optional[str] = Field(None, description="Review comment (stored as 'body' in DB)")
    mood: Optional[str] = Field(None, description="Optional user mood as free text")


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    mood: Optional[str] = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: str
    book_id: Union[str, int]
    user_id: str

    rating: int

    # DB fields (optional)
    title: Optional[str] = None
    body: Optional[str] = None

    # API-friendly alias
    comment: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_orm_with_comment(review_obj) -> "ReviewOut":
        """
        Helper: if the ORM object uses 'body' but the API wants 'comment'.
        """
        data = ReviewOut.model_validate(review_obj).model_dump()
        if data.get("comment") is None:
            data["comment"] = data.get("body")
        return ReviewOut(**data)
