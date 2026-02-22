from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.services.book_service import BookService
from app.services.review_service import ReviewService
from app.services.bookshelf_service import BookshelfService
from app.services.mood_recommendation.recommendation_engine import RecommendationEngine
from app.schemas.book import BookRead


router = APIRouter()


class ContentBasedRequest(BaseModel):
    user_id: str
    book_id: str
    rating: int
    review_text: Optional[str] = None


class CollaborativeRequest(BaseModel):
    user_id: str
    book_id: str
    review_text: Optional[str] = None


class RecommendationItem(BaseModel):
    book: BookRead
    score: Optional[float] = None
    similarity: Optional[float] = None
    contrast_score: Optional[float] = None


def get_recommendation_engine(db: Session = Depends(get_db)) -> RecommendationEngine:
    """Create a RecommendationEngine wired to app services using the request DB session."""
    book_service = BookService(db)
    review_service = ReviewService(db)
    bookshelf_service = BookshelfService(db)
    return RecommendationEngine(
        book_service=book_service,
        review_service=review_service,
        bookshelf_service=bookshelf_service,
        db=db,
    )


@router.post(
    "/content-based",
    response_model=List[RecommendationItem],
    status_code=status.HTTP_200_OK,
)
def recommend_content_based(
    payload: ContentBasedRequest,
    db: Session = Depends(get_db),
    engine: RecommendationEngine = Depends(get_recommendation_engine),
):
    """
    Generate content-based recommendations driven by emotion profiles.

    Body: {user_id, book_id, rating, review_text}
    Returns up to 5 recommendations with similarity scores. In contrast mode,
    items also include `contrast_score`.
    """
    try:
        recs = engine.recommend_content_based(
            user_id=payload.user_id,
            book_id=payload.book_id,
            rating=payload.rating,
            review_text=payload.review_text or "",
        )

        # Normalize to RecommendationItem list
        out = []
        for r in recs:
            item = {
                "book": r.get("book"),
                "score": r.get("similarity") if r.get("similarity") is not None else r.get("score"),
                "similarity": r.get("similarity"),
                "contrast_score": r.get("contrast_score"),
            }
            out.append(item)
        return out
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/collaborative",
    response_model=List[RecommendationItem],
    status_code=status.HTTP_200_OK,
)
def recommend_collaborative(
    payload: CollaborativeRequest,
    db: Session = Depends(get_db),
    engine: RecommendationEngine = Depends(get_recommendation_engine),
):
    """
    Generate collaborative recommendations based on similar users' preferences.

    Body: {user_id, book_id, review_text}
    Returns up to 5 recommendations ranked by a personalized weighted score.
    """
    try:
        recs = engine.recommend_collaborative(
            user_id=payload.user_id,
            book_id=payload.book_id,
            review_text=payload.review_text or "",
        )

        out = []
        for r in recs:
            # r expected: {"book": <Book>, "score": <float>} from engine
            item = {
                "book": r.get("book"),
                "score": r.get("score"),
                "similarity": r.get("similarity"),
            }
            out.append(item)
        return out
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ DEBUG ENDPOINTS ============

@router.get("/debug/books")
def debug_get_all_books(db: Session = Depends(get_db)):
    """
    DEBUG: List all books in the database.
    Returns: List of books with IDs and titles.
    """
    try:
        book_service = BookService(db)
        books = book_service.get_books()
        return {
            "total_books": len(books),
            "books": [
                {"book_id": b.book_id, "title": b.title}
                for b in books
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching books: {str(e)}")


@router.get("/debug/user/{user_id}/bookshelf")
def debug_get_user_bookshelf(user_id: str, db: Session = Depends(get_db)):
    """
    DEBUG: List books the user has read/added to their bookshelf.
    Returns: List of books on user's shelf with status.
    """
    try:
        bookshelf_service = BookshelfService(db)
        read_items = bookshelf_service.list_shelf(user_id=user_id, status="read")
        all_items = bookshelf_service.list_shelf(user_id=user_id)
        
        return {
            "user_id": user_id,
            "total_shelf_items": len(all_items),
            "read_books_count": len(read_items),
            "all_shelf_items": [
                {"book_id": item.book_id, "status": item.shelf_status}
                for item in all_items
            ],
            "read_books": [
                {"book_id": item.book_id, "status": item.shelf_status}
                for item in read_items
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching user shelf: {str(e)}")


@router.get("/debug/book/{book_id}/emotions")
def debug_get_book_emotions(book_id: str, db: Session = Depends(get_db)):
    """
    DEBUG: Get emotion profile for a specific book.
    Returns: Emotion scores and counts based on reviews.
    """
    try:
        book_service = BookService(db)
        review_service = ReviewService(db)
        engine = get_recommendation_engine(db)
        
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        reviews = review_service.get_reviews_by_book_id(book_id, limit=500)
        review_texts = [getattr(r, "body", None) or getattr(r, "comment", None) or "" for r in reviews]
        
        emotion_profile = engine.get_emotion_profile(book_id, book.title, review_texts)
        
        return {
            "book_id": book_id,
            "book_title": book.title,
            "num_reviews": len(reviews),
            "emotion_profile": emotion_profile
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching emotion profile: {str(e)}")


@router.get("/debug/book/{book_id}/reviews")
def debug_get_book_reviews(book_id: str, db: Session = Depends(get_db)):
    """
    DEBUG: Get reviews for a specific book.
    Returns: List of reviews with user IDs and ratings.
    """
    try:
        book_service = BookService(db)
        review_service = ReviewService(db)
        
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        reviews = review_service.get_reviews_by_book_id(book_id, limit=500)
        avg_rating = review_service.get_average_rating(book_id)
        
        return {
            "book_id": book_id,
            "book_title": book.title,
            "total_reviews": len(reviews),
            "average_rating": avg_rating,
            "reviews": [
                {
                    "review_id": r.review_id,
                    "user_id": r.user_id,
                    "rating": r.rating,
                    "body": r.body or getattr(r, "comment", None),
                }
                for r in reviews
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching reviews: {str(e)}")
