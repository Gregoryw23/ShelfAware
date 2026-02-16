from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class BookshelfCreate(BaseModel):
    book_id: str = Field(..., description="UUID of the book")
    shelf_status: str = Field(default="want_to_read", description="want_to_read | reading | finished")

class BookshelfUpdate(BaseModel):
    shelf_status: Optional[str] = None
    date_started: Optional[datetime] = None
    date_finished: Optional[datetime] = None

class BookshelfRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    book_id: str
    shelf_status: str
    date_added: datetime
    date_started: Optional[datetime] = None
    date_finished: Optional[datetime] = None
    updated_at: datetime
    synopsis: Optional[str] = None