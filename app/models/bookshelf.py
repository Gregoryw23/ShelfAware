import uuid, pydantic
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Bookshelf(Base):
    __tablename__ = "bookshelf"

    user_id = Column(String, ForeignKey("user.user_id"), primary_key=True, index=True)
    book_id = Column(String, ForeignKey("book.book_id"), primary_key=True)

    shelf_status = Column(String, nullable=False, default="want_to_read")
    date_added = Column(DateTime, nullable=False, default=datetime)
    date_started = Column(DateTime, nullable=True)
    date_finished = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime, onupdate=datetime)
    synopsis = Column(String, nullable=True)
    
    # Relationship with user
    user = relationship("User", back_populates="bookshelf")
    
    # Relationship with book
    book = relationship("Book", back_populates="bookshelves")


from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

# Pydantic Models for Request/Response
class BookshelfBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100, description="The title of the book (3-100 characters)")
    author: str = Field(..., min_length=3, max_length=50, description="The author of the book (3-50 characters)")
    year: int = Field(..., gt=0, description="The publication year of the book (must be positive)")
    description: str = Field(..., min_length=10, max_length=1000, description="The description of the book (10-1000 characters)")

#class BookInfo(BookBase):
#    pass