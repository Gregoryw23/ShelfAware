from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Union
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
    model_config = ConfigDict(from_attributes=True)
    
    review_id: str
    book_id: Union[str, int]
    user_id: str

    rating: int
    title: Optional[str] = None
    body: Optional[str] = None

    created_at: datetime
    updated_at: datetime
        
