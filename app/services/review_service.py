from __future__ import annotations
from typing import Sequence
from uuid import UUID
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.review import Review
from app.models.book import Book
from app.models.user import User
from app.models.mood import Mood  # imported for mood handling

from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewOut


class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    # --- Internal Helpers ---
    def _ensure_book_exists(self, book_id: UUID) -> None:
        exists = self.db.scalar(select(Book.book_id).where(Book.book_id == book_id))
        if not exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    def _ensure_user_exists(self, user_id: UUID) -> None:
        exists = self.db.scalar(select(User.user_id).where(User.user_id == user_id))
        if not exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    def _get_review_or_404(self, review_id: UUID) -> Review:
        review = self.db.get(Review, review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        return review

    # --- Commands ---
    def add_review(self, *, book_id: UUID, user_id: UUID, review_data: ReviewCreate) -> Review:
        self._ensure_book_exists(book_id)
        self._ensure_user_exists(user_id)

        payload = review_data.model_dump()
        rating = payload.get("rating")
        if rating is None or not (1 <= rating <= 5):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Rating must be between 1 and 5"
            )

        # Create review
        review = Review(book_id=book_id, user_id=user_id, **payload)
        self.db.add(review)

        # --- Mood handling ---
        mood_text = payload.get("mood")
        if mood_text:
            mood_entry = Mood(user_id=user_id, mood=mood_text, mood_date=date.today())
            self.db.add(mood_entry)

        try:
            self.db.commit()
            self.db.refresh(review)
            return review
        except IntegrityError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reviewed this book."
            ) from e

    def update_review(self, review_id: UUID, acting_user_id: UUID, review_data: ReviewUpdate) -> Review:
        self._ensure_user_exists(acting_user_id)

        review = self._get_review_or_404(review_id)

        if review.user_id != acting_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this review")

        update_data = review_data.model_dump(exclude_unset=True)

        # Validate rating if provided
        if "rating" in update_data and update_data["rating"] is not None:
            rating = update_data["rating"]
            if not (1 <= rating <= 5):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rating must be between 1 and 5")

        # Update review fields except mood
        for key, value in update_data.items():
            if key != "mood":
                setattr(review, key, value)

        # --- Mood update ---
        mood_text = update_data.get("mood")
        if mood_text is not None:
            existing_mood = self.db.scalar(
                select(Mood).where(Mood.user_id == acting_user_id, Mood.mood_date == date.today())
            )
            if existing_mood:
                existing_mood.mood = mood_text
            else:
                self.db.add(Mood(user_id=acting_user_id, mood=mood_text, mood_date=date.today()))

        self.db.commit()
        self.db.refresh(review)
        return review

    def delete_review(self, review_id: UUID, acting_user_id: UUID) -> None:
        self._ensure_user_exists(acting_user_id)

        review = self._get_review_or_404(review_id)
        if review.user_id != acting_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this review")

        self.db.delete(review)
        self.db.commit()

    # --- Queries ---
    def get_reviews_by_book_id(
        self,
        book_id: UUID,
        limit: int = 20,
        offset: int = 0,
        newest_first: bool = True,
    ) -> Sequence[Review]:
        self._ensure_book_exists(book_id)
        stmt = (
            select(Review)
            .where(Review.book_id == book_id)
            .order_by(Review.created_at.desc() if newest_first else Review.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return self.db.scalars(stmt).all()

    def get_average_rating(self, book_id: UUID) -> float | None:
        self._ensure_book_exists(book_id)
        avg = self.db.scalar(select(func.avg(Review.rating)).where(Review.book_id == book_id))
        return round(float(avg), 2) if avg is not None else None
