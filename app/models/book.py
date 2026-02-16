import uuid, pydantic
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Integer, Date
from sqlalchemy.orm import relationship
from app.db.database import Base

class Book(Base):
    __tablename__ = "book"

    book_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)

    subtitle = Column(String, nullable=True)
    cover_image_url = Column(String, nullable=True)

    abstract = Column(String, nullable=True)
    CommunitySynopsis = Column(String, nullable=True)

    page_count = Column(Integer, nullable=True)
    published_date = Column(Date, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    bookshelves = relationship(
        "Bookshelf",
        back_populates="book",
        cascade="all, delete-orphan"
    )

    reviews = relationship(
        "Review",
        back_populates="book",
        cascade="all, delete-orphan"
    )

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class BookBase(BaseModel):
    title: str
    subtitle: Optional[str] = None
    cover_image_url: Optional[str] = None
    abstract: Optional[str] = None
    page_count: Optional[int] = None
    published_date: Optional[date] = None
    CommunitySynopsis: Optional[str] = None

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