#Code 3
# app/routes/review.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies.db import get_db
from app.services.review_service import ReviewService
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewOut
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter()


# --- Dependency to get ReviewService ---
def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db=db)


def resolve_user_id(current_user: dict, db: Session) -> str:
    """
    Resolve application user_id from current_user (dict).

    - If get_current_user() already returns user_id -> use it.
    - Else, try using cognito sub from token claims (sub / cognito_sub)
      and look up user in DB.
    """
    user_id = current_user.get("user_id") or current_user.get("id")
    if user_id:
        return str(user_id)

    sub = current_user.get("cognito_sub") or current_user.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token (missing user_id/sub).",
        )

    user = db.query(User).filter(User.cognito_sub == sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user not found in database.",
        )

    return str(user.user_id)


# --- Create a review ---
@router.post(
    "/books/{book_id}",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    book_id: str,
    review_data: ReviewCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: ReviewService = Depends(get_review_service),
):
    """
    Create a new review for a book.
    User is derived from authentication token (do NOT pass user_id).
    """
    user_id = resolve_user_id(current_user, db)

    review = service.add_review(
        book_id=book_id,
        user_id=user_id,
        review_data=review_data,
    )

    # ✅ Ensure API response has `comment` even though DB stores `body`
    return ReviewOut.from_orm_with_comment(review)


# --- Get all reviews for a specific book (paginated) ---
@router.get("/book/{book_id}", response_model=List[ReviewOut])
def get_reviews_for_book(
    book_id: str,
    limit: int = 20,
    offset: int = 0,
    newest_first: bool = True,
    service: ReviewService = Depends(get_review_service),
):
    """
    Get reviews for a specific book with pagination.
    """
    reviews = service.get_reviews_by_book_id(
        book_id=book_id,
        limit=limit,
        offset=offset,
        newest_first=newest_first,
    )

    return [ReviewOut.from_orm_with_comment(r) for r in reviews]


# --- Get a single review by ID ---
@router.get("/{review_id}", response_model=ReviewOut)
def get_review(
    review_id: str,
    service: ReviewService = Depends(get_review_service),
):
    """
    Retrieve a single review by its ID.
    """
    review = service._get_review_or_404(review_id)
    return ReviewOut.from_orm_with_comment(review)


# --- Update a review ---
@router.put("/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: str,
    review_data: ReviewUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: ReviewService = Depends(get_review_service),
):
    """
    Update a review. Only the creator can update it.
    Acting user is derived from token (do NOT pass acting_user_id).
    """
    acting_user_id = resolve_user_id(current_user, db)

    review = service.update_review(
        review_id=review_id,
        acting_user_id=acting_user_id,
        review_data=review_data,
    )

    return ReviewOut.from_orm_with_comment(review)


# --- Delete a review ---
@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: ReviewService = Depends(get_review_service),
):
    """
    Delete a review. Only the creator can delete it.
    Acting user is derived from token (do NOT pass acting_user_id).
    """
    acting_user_id = resolve_user_id(current_user, db)

    service.delete_review(
        review_id=review_id,
        acting_user_id=acting_user_id,
    )
    return None



#Code 2
# app/routes/review.py
'''
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies.db import get_db
from app.services.review_service import ReviewService
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewOut
from app.dependencies.auth import get_current_user

router = APIRouter()


# --- Dependency to get ReviewService ---
def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db=db)


def _get_user_id_from_current_user(current_user: dict) -> str:
    """
    get_current_user() returns a dict (based on your earlier errors).
    We normalize how to extract user_id here.
    """
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token (missing user_id).",
        )
    return user_id


# --- Create a review ---
@router.post("/books/{book_id}", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    book_id: str,
    review_data: ReviewCreate,
    current_user: dict = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """
    Create a new review for a book.
    User is derived from authentication token (do NOT pass user_id).
    """
    user_id = _get_user_id_from_current_user(current_user)

    return service.add_review(
        book_id=book_id,
        user_id=user_id,
        review_data=review_data,
    )


# --- Get all reviews for a specific book (paginated) ---
@router.get("/book/{book_id}", response_model=List[ReviewOut])
def get_reviews_for_book(
    book_id: str,
    limit: int = 20,
    offset: int = 0,
    newest_first: bool = True,
    service: ReviewService = Depends(get_review_service),
):
    """
    Get reviews for a specific book with pagination.
    """
    return service.get_reviews_by_book_id(
        book_id=book_id,
        limit=limit,
        offset=offset,
        newest_first=newest_first,
    )


# --- Get a single review by ID ---
@router.get("/{review_id}", response_model=ReviewOut)
def get_review(
    review_id: str,
    service: ReviewService = Depends(get_review_service),
):
    """
    Retrieve a single review by its ID.
    """
    return service._get_review_or_404(review_id)


# --- Update a review ---
@router.put("/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: str,
    review_data: ReviewUpdate,
    current_user: dict = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """
    Update a review. Only the creator can update it.
    Acting user is derived from token (do NOT pass acting_user_id).
    """
    acting_user_id = _get_user_id_from_current_user(current_user)

    return service.update_review(
        review_id=review_id,
        acting_user_id=acting_user_id,
        review_data=review_data,
    )


# --- Delete a review ---
@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: str,
    current_user: dict = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """
    Delete a review. Only the creator can delete it.
    Acting user is derived from token (do NOT pass acting_user_id).
    """
    acting_user_id = _get_user_id_from_current_user(current_user)

    service.delete_review(
        review_id=review_id,
        acting_user_id=acting_user_id,
    )
    return None
'''

#Code 1
'''
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.services.review_service import ReviewService
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewOut
from app.dependencies.auth import get_current_user  
from app.models.user import User  


router = APIRouter()


# --- Dependency to get ReviewService ---
def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db=db)


# --- Create a review ---
@router.post("/books/{book_id}", response_model=ReviewOut)
def create_review(
    book_id: str,
    user_id: str,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),  # from auth
    service: ReviewService = Depends(get_review_service)
):
    """
    Create a new review for a book.
    User is derived from authentication token.
    """
    return service.add_review(
        book_id=book_id,
        user_id=current_user.id,  # injected securely
        review_data=review_data
    )


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
    current_user: User = Depends(get_current_user),  
    service: ReviewService = Depends(get_review_service)
):
    """
    Update a review. Only the creator can update it.
    """
    return service.update_review(
        review_id=review_id,
        acting_user_id=current_user.id, 
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
    Delete a review. Only the creator can delete it.
    """
    service.delete_review(
        review_id=review_id,
        acting_user_id=current_user.id  
    )
    return None
'''
