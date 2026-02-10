from fastapi import Depends
from app.services.book_service import BookService
from app.services.review_service import ReviewService
from app.dependencies.db import get_db
from sqlalchemy.orm import Session

def get_book_service(db: Session = Depends(get_db)) -> BookService:
    return BookService(db)

def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db)

