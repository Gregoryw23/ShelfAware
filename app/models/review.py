# app/models/review.py

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

from app.db.database import Base


def new_uuid():
    return str(uuid.uuid4())


class Review(Base):
    __tablename__ = "reviews"

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        UniqueConstraint("user_id", "book_id", name="uq_reviews_user_book"),
        Index("ix_reviews_book_id", "book_id"),
        Index("ix_reviews_user_id", "user_id"),
    )

    review_id = Column(String, primary_key=True, default=new_uuid, index=True)

    user_id = Column(String, ForeignKey("user.user_id"), nullable=False)
    book_id = Column(String, ForeignKey("book.book_id"), nullable=False)

    rating = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
