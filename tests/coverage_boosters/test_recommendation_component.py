from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routes import recommendation_routes as rec_routes


def test_recommendation_engine_dependency_factory(db):
    engine = rec_routes.get_recommendation_engine(db)
    assert engine.db is db


def test_recommend_content_based_success_and_error(db):
    payload = rec_routes.ContentBasedRequest(user_id="u1", book_id="b1", rating=5, review_text="good")

    class _EngineOk:
        def recommend_content_based(self, **kwargs):
            return [{"book": _book_obj("b1", "Book One"), "similarity": 0.9, "contrast_score": 0.2}]

    out = rec_routes.recommend_content_based(payload, db, _EngineOk())
    assert len(out) == 1
    assert out[0]["similarity"] == 0.9

    class _EngineErr:
        def recommend_content_based(self, **kwargs):
            raise RuntimeError("bad")

    with pytest.raises(HTTPException) as exc:
        rec_routes.recommend_content_based(payload, db, _EngineErr())
    assert exc.value.status_code == 400


def test_recommend_collaborative_success_and_error(db):
    payload = rec_routes.CollaborativeRequest(user_id="u1", book_id="b1", review_text="nice")

    class _EngineOk:
        def recommend_collaborative(self, **kwargs):
            return [{"book": _book_obj("b2", "Book Two"), "score": 0.8}]

    out = rec_routes.recommend_collaborative(payload, db, _EngineOk())
    assert len(out) == 1
    assert out[0]["score"] == 0.8

    class _EngineErr:
        def recommend_collaborative(self, **kwargs):
            raise RuntimeError("bad")

    with pytest.raises(HTTPException) as exc:
        rec_routes.recommend_collaborative(payload, db, _EngineErr())
    assert exc.value.status_code == 400


def test_recommendation_debug_endpoints(monkeypatch, db):
    class _BookService:
        def __init__(self, _db):
            pass

        def get_books(self):
            return [_book_obj("b1", "Book One")]

        def get_book(self, _book_id):
            return _book_obj("b1", "Book One")

    class _ReviewObj:
        def __init__(self):
            self.review_id = "r1"
            self.user_id = "u1"
            self.rating = 5
            self.body = "great"
            self.comment = None

    class _ReviewService:
        def __init__(self, _db):
            pass

        def get_reviews_by_book_id(self, *args, **kwargs):
            return [_ReviewObj()]

        def get_average_rating(self, _book_id):
            return 5.0

    class _ShelfItem:
        def __init__(self, book_id, shelf_status):
            self.book_id = book_id
            self.shelf_status = shelf_status

    class _BookshelfService:
        def __init__(self, _db):
            pass

        def list_shelf(self, user_id, status=None):
            if status == "read":
                return [_ShelfItem("b1", "read")]
            return [_ShelfItem("b1", "read"), _ShelfItem("b2", "want_to_read")]

    class _Engine:
        def get_emotion_profile(self, *args, **kwargs):
            return {"joy": 0.7}

    monkeypatch.setattr(rec_routes, "BookService", _BookService)
    monkeypatch.setattr(rec_routes, "ReviewService", _ReviewService)
    monkeypatch.setattr(rec_routes, "BookshelfService", _BookshelfService)
    monkeypatch.setattr(rec_routes, "get_recommendation_engine", lambda _db: _Engine())

    books = rec_routes.debug_get_all_books(db)
    shelf = rec_routes.debug_get_user_bookshelf("u1", db)
    emo = rec_routes.debug_get_book_emotions("b1", db)
    rev = rec_routes.debug_get_book_reviews("b1", db)

    assert books["total_books"] == 1
    assert shelf["read_books_count"] == 1
    assert emo["emotion_profile"]["joy"] == 0.7
    assert rev["average_rating"] == 5.0


def test_recommendation_debug_endpoints_errors(monkeypatch, db):
    class _BookServiceMissing:
        def __init__(self, _db):
            pass

        def get_book(self, _book_id):
            return None

        def get_books(self):
            raise RuntimeError("db err")

    class _ReviewService:
        def __init__(self, _db):
            pass

        def get_reviews_by_book_id(self, *args, **kwargs):
            return []

        def get_average_rating(self, _book_id):
            return 0

    class _BookshelfService:
        def __init__(self, _db):
            pass

        def list_shelf(self, *args, **kwargs):
            raise RuntimeError("err")

    monkeypatch.setattr(rec_routes, "BookService", _BookServiceMissing)
    monkeypatch.setattr(rec_routes, "ReviewService", _ReviewService)
    monkeypatch.setattr(rec_routes, "BookshelfService", _BookshelfService)

    with pytest.raises(HTTPException):
        rec_routes.debug_get_all_books(db)
    with pytest.raises(HTTPException):
        rec_routes.debug_get_user_bookshelf("u1", db)
    with pytest.raises(HTTPException):
        rec_routes.debug_get_book_emotions("missing", db)
    with pytest.raises(HTTPException):
        rec_routes.debug_get_book_reviews("missing", db)


def _book_obj(book_id: str, title: str):
    return SimpleNamespace(
        book_id=book_id,
        title=title,
        subtitle=None,
        cover_image_url=None,
        abstract=None,
        page_count=100,
        published_date=None,
        created_at=datetime.utcnow(),
    )
