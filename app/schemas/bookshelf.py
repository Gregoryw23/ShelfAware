from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

ShelfStatus = Literal["want_to_read", "currently_reading", "read"]


class BookshelfCreate(BaseModel):
    book_id: str = Field(..., min_length=1)


class BookshelfStatusUpdate(BaseModel):
    shelf_status: ShelfStatus


class BookshelfRead(BaseModel):
    user_id: str
    book_id: str
    shelf_status: ShelfStatus
    date_added: datetime
    date_started: Optional[datetime] = None
    date_finished: Optional[datetime] = None
    updated_at: datetime
    synopsis: Optional[str] = None

    class Config:
        from_attributes = True  # Pydantic v2 compatibility