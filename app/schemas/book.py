from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional

class BookBase(BaseModel):
    title: str
    subtitle: Optional[str] = None
    cover_image_url: Optional[str] = None
    abstract: Optional[str] = None
    page_count: Optional[int] = None
    published_date: Optional[date] = None

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    cover_image_url: Optional[str] = None
    abstract: Optional[str] = None
    page_count: Optional[int] = None
    published_date: Optional[date] = None

class BookRead(BookBase):
    book_id: str
    created_at: datetime

    class Config:
        from_attributes = True  # <-- critical for SQLAlchemy
