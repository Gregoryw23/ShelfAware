from unittest.mock import MagicMock

from app.dependencies.services import get_book_service, get_review_service
from app.services.book_service import BookService
from app.services.review_service import ReviewService


def test_get_book_service_returns_book_service_with_db():
    db = MagicMock()

    service = get_book_service(db=db)

    assert isinstance(service, BookService)
    assert service.db is db


def test_get_review_service_returns_review_service_with_db():
    db = MagicMock()

    service = get_review_service(db=db)

    assert isinstance(service, ReviewService)
    assert service.db is db
