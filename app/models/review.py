from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    CheckConstraint,
    UniqueConstraint,
    Index,
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pydantic import BaseModel, ConfigDict

from app.db.database import Base
from app.models.book import Book
from app.models.user import User  

def new_uuid():
    return str(uuid.uuid4())

class Review(Base):
    __tablename__ = "reviews"

    __table_args__ = (
        # DB-enforced rating bounds
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        # One review per user per book
        UniqueConstraint("user_id", "book_id", name="uq_reviews_user_book"),
        # Helpful indexes
        Index("ix_reviews_book_id", "book_id"),
        Index("ix_reviews_user_id", "user_id"),
    )

    review_id = Column(String, primary_key=True, default=new_uuid, index=True)

    user_id = Column(String, ForeignKey("user.user_id"), nullable=False)

    book_id = Column(String, ForeignKey("book.book_id"), nullable=False)

    rating = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)

    # Use server-managed, timezone-aware timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")  

# --------------------
# Pydantic Schemas
# --------------------

class ReviewBase(BaseModel):
    rating: int
    title: str | None = None
    body: str | None = None

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: int | None = None
    title: str | None = None
    body: str | None = None

class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    review_id: str
    user_id: str
    book_id: str
    created_at: datetime
    updated_at: datetime
