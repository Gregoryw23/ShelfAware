# app/routes/review.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db  # DB session dependency
from app.services.review_service import ReviewService
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewOut  # Pydantic schemas

router = APIRouter()

# --- Dependency to get ReviewService ---
def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db=db)


# --- Create a review ---
@router.post("/", response_model=ReviewOut)
def create_review(
    book_id: str,
    user_id: str,
    review_data: ReviewCreate,
    service: ReviewService = Depends(get_review_service)
):
    """
    Create a new review for a book.
    Optional: user can submit a 'mood' as free text via review_data.mood.
    """
    return service.add_review(book_id=book_id, user_id=user_id, review_data=review_data)


# --- Get all reviews for a specific book (paginated) ---
@router.get("/book/{book_id}", response_model=List[ReviewOut])
def get_reviews_for_book(
    book_id: str,
    limit: int = 20,
    offset: int = 0,
    newest_first: bool = True,
    service: ReviewService = Depends(get_review_service)
):
    """
    Get reviews for a specific book with pagination.
    """
    return service.get_reviews_by_book_id(
        book_id=book_id,
        limit=limit,
        offset=offset,
        newest_first=newest_first
    )


# --- Get a single review by ID ---
@router.get("/{review_id}", response_model=ReviewOut)
def get_review(
    review_id: str,
    service: ReviewService = Depends(get_review_service)
):
    """
    Retrieve a single review by its ID.
    """
    return service._get_review_or_404(review_id)


# --- Update a review ---
@router.put("/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: str,
    acting_user_id: str,
    review_data: ReviewUpdate,
    service: ReviewService = Depends(get_review_service)
):
    """
    Update a review. Only the user who created the review can update it.
    Optional: user can update their mood via review_data.mood.
    """
    return service.update_review(
        review_id=review_id,
        acting_user_id=acting_user_id,
        review_data=review_data
    )


# --- Delete a review ---
@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: str,
    acting_user_id: str,
    service: ReviewService = Depends(get_review_service)
):
    """
    Delete a review. Only the user who created the review can delete it.
    """
    service.delete_review(review_id=review_id, acting_user_id=acting_user_id)
    return None


