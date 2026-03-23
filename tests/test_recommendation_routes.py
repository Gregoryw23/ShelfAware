from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.book import Book
from app.routes import recommendation_routes


def make_book(book_id="book-1", title="Book One"):
    return Book(book_id=book_id, title=title, created_at=datetime.utcnow())


def test_get_recommendation_engine_wires_services():
    db = object()

    with patch.object(recommendation_routes, "BookService") as mock_book_service, patch.object(
        recommendation_routes, "ReviewService"
    ) as mock_review_service, patch.object(
        recommendation_routes, "BookshelfService"
    ) as mock_bookshelf_service, patch.object(
        recommendation_routes, "RecommendationEngine"
    ) as mock_engine:
        recommendation_routes.get_recommendation_engine(db)

    mock_book_service.assert_called_once_with(db)
    mock_review_service.assert_called_once_with(db)
    mock_bookshelf_service.assert_called_once_with(db)
    mock_engine.assert_called_once()


def test_recommend_content_based_normalizes_similarity_and_score():
    payload = recommendation_routes.ContentBasedRequest(
        user_id="u1",
        book_id="b1",
        rating=5,
        review_text=None,
    )
    engine = MagicMock()
    book = make_book("b2", "Similar Book")
    engine.recommend_content_based.return_value = [
        {"book": book, "similarity": 0.8, "contrast_score": 0.2},
        {"book": book, "score": 4.5, "similarity": None},
    ]

    result = recommendation_routes.recommend_content_based(payload, db=object(), engine=engine)

    assert result[0]["score"] == 0.8
    assert result[0]["similarity"] == 0.8
    assert result[0]["contrast_score"] == 0.2
    assert result[1]["score"] == 4.5
    engine.recommend_content_based.assert_called_once_with(
        user_id="u1",
        book_id="b1",
        rating=5,
        review_text="",
    )


def test_recommend_content_based_wraps_errors():
    payload = recommendation_routes.ContentBasedRequest(user_id="u1", book_id="b1", rating=1, review_text="oops")
    engine = MagicMock()
    engine.recommend_content_based.side_effect = RuntimeError("boom")

    with pytest.raises(HTTPException, match="boom") as exc:
        recommendation_routes.recommend_content_based(payload, db=object(), engine=engine)

    assert exc.value.status_code == 400


def test_recommend_collaborative_normalizes_output():
    payload = recommendation_routes.CollaborativeRequest(user_id="u1", book_id="b1", review_text=None)
    engine = MagicMock()
    book = make_book("b2", "Collaborative Book")
    engine.recommend_collaborative.return_value = [{"book": book, "score": 4.1, "similarity": 0.9}]

    result = recommendation_routes.recommend_collaborative(payload, db=object(), engine=engine)

    assert result == [{"book": book, "score": 4.1, "similarity": 0.9}]
    engine.recommend_collaborative.assert_called_once_with(user_id="u1", book_id="b1", review_text="")


def test_recommend_collaborative_wraps_errors():
    payload = recommendation_routes.CollaborativeRequest(user_id="u1", book_id="b1", review_text="text")
    engine = MagicMock()
    engine.recommend_collaborative.side_effect = ValueError("bad collaborative input")

    with pytest.raises(HTTPException, match="bad collaborative input") as exc:
        recommendation_routes.recommend_collaborative(payload, db=object(), engine=engine)

    assert exc.value.status_code == 400


def test_debug_get_all_books_success():
    books = [make_book("b1", "One"), make_book("b2", "Two")]

    with patch.object(recommendation_routes, "BookService") as mock_book_service:
        mock_book_service.return_value.get_books.return_value = books

        result = recommendation_routes.debug_get_all_books(db=object())

    assert result["total_books"] == 2
    assert result["books"] == [{"book_id": "b1", "title": "One"}, {"book_id": "b2", "title": "Two"}]


def test_debug_get_all_books_wraps_errors():
    with patch.object(recommendation_routes, "BookService") as mock_book_service:
        mock_book_service.return_value.get_books.side_effect = RuntimeError("db fail")

        with pytest.raises(HTTPException, match="Error fetching books: db fail") as exc:
            recommendation_routes.debug_get_all_books(db=object())

    assert exc.value.status_code == 400


def test_debug_get_user_bookshelf_success():
    read_item = SimpleNamespace(book_id="b1", shelf_status="read")
    want_item = SimpleNamespace(book_id="b2", shelf_status="want_to_read")

    with patch.object(recommendation_routes, "BookshelfService") as mock_service:
        mock_service.return_value.list_shelf.side_effect = [[read_item], [read_item, want_item]]

        result = recommendation_routes.debug_get_user_bookshelf("u1", db=object())

    assert result["user_id"] == "u1"
    assert result["read_books_count"] == 1
    assert result["total_shelf_items"] == 2
    assert result["all_shelf_items"] == [
        {"book_id": "b1", "status": "read"},
        {"book_id": "b2", "status": "want_to_read"},
    ]


def test_debug_get_user_bookshelf_wraps_errors():
    with patch.object(recommendation_routes, "BookshelfService") as mock_service:
        mock_service.return_value.list_shelf.side_effect = RuntimeError("shelf error")

        with pytest.raises(HTTPException, match="Error fetching user shelf: shelf error") as exc:
            recommendation_routes.debug_get_user_bookshelf("u1", db=object())

    assert exc.value.status_code == 400


def test_debug_get_book_emotions_success():
    book = make_book("b1", "Mood Book")
    reviews = [SimpleNamespace(body="body 1", comment=None), SimpleNamespace(body=None, comment="comment 2")]
    engine = MagicMock()
    engine.get_emotion_profile.return_value = {"emotion_scores": {"joy": 100.0}}

    with patch.object(recommendation_routes, "BookService") as mock_book_service, patch.object(
        recommendation_routes, "ReviewService"
    ) as mock_review_service, patch.object(
        recommendation_routes, "get_recommendation_engine",
        return_value=engine,
    ):
        mock_book_service.return_value.get_book.return_value = book
        mock_review_service.return_value.get_reviews_by_book_id.return_value = reviews

        result = recommendation_routes.debug_get_book_emotions("b1", db=object())

    assert result["book_id"] == "b1"
    assert result["num_reviews"] == 2
    assert result["emotion_profile"] == {"emotion_scores": {"joy": 100.0}}
    engine.get_emotion_profile.assert_called_once_with("b1", "Mood Book", ["body 1", "comment 2"])


def test_debug_get_book_emotions_reraises_http_errors():
    with patch.object(recommendation_routes, "BookService") as mock_book_service:
        mock_book_service.return_value.get_book.return_value = None

        with pytest.raises(HTTPException, match="Book not found") as exc:
            recommendation_routes.debug_get_book_emotions("missing", db=object())

    assert exc.value.status_code == 404


def test_debug_get_book_emotions_wraps_generic_errors():
    with patch.object(recommendation_routes, "BookService") as mock_book_service, patch.object(
        recommendation_routes, "ReviewService"
    ) as mock_review_service, patch.object(
        recommendation_routes, "get_recommendation_engine"
    ) as mock_engine_factory:
        mock_book_service.return_value.get_book.return_value = make_book("b1", "Book")
        mock_review_service.return_value.get_reviews_by_book_id.return_value = []
        mock_engine_factory.return_value.get_emotion_profile.side_effect = RuntimeError("profile fail")

        with pytest.raises(HTTPException, match="Error fetching emotion profile: profile fail") as exc:
            recommendation_routes.debug_get_book_emotions("b1", db=object())

    assert exc.value.status_code == 400


def test_debug_get_book_reviews_success():
    book = make_book("b1", "Review Book")
    reviews = [
        SimpleNamespace(review_id="r1", user_id="u1", rating=5, body="body", comment=None),
        SimpleNamespace(review_id="r2", user_id="u2", rating=4, body=None, comment="comment"),
    ]

    with patch.object(recommendation_routes, "BookService") as mock_book_service, patch.object(
        recommendation_routes, "ReviewService"
    ) as mock_review_service:
        mock_book_service.return_value.get_book.return_value = book
        mock_review_service.return_value.get_reviews_by_book_id.return_value = reviews
        mock_review_service.return_value.get_average_rating.return_value = 4.5

        result = recommendation_routes.debug_get_book_reviews("b1", db=object())

    assert result["book_title"] == "Review Book"
    assert result["average_rating"] == 4.5
    assert result["reviews"] == [
        {"review_id": "r1", "user_id": "u1", "rating": 5, "body": "body"},
        {"review_id": "r2", "user_id": "u2", "rating": 4, "body": "comment"},
    ]


def test_debug_get_book_reviews_reraises_http_errors():
    with patch.object(recommendation_routes, "BookService") as mock_book_service:
        mock_book_service.return_value.get_book.return_value = None

        with pytest.raises(HTTPException, match="Book not found") as exc:
            recommendation_routes.debug_get_book_reviews("missing", db=object())

    assert exc.value.status_code == 404


def test_debug_get_book_reviews_wraps_generic_errors():
    with patch.object(recommendation_routes, "BookService") as mock_book_service, patch.object(
        recommendation_routes, "ReviewService"
    ) as mock_review_service:
        mock_book_service.return_value.get_book.return_value = make_book("b1", "Book")
        mock_review_service.return_value.get_reviews_by_book_id.side_effect = RuntimeError("review fail")

        with pytest.raises(HTTPException, match="Error fetching reviews: review fail") as exc:
            recommendation_routes.debug_get_book_reviews("b1", db=object())

    assert exc.value.status_code == 400
