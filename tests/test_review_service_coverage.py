from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.review_service import ReviewService


class _Payload:
    def __init__(self, data):
        self._data = data

    def model_dump(self, exclude_unset=True):
        return dict(self._data)


def test_ensure_book_exists_success_and_not_found():
    db = MagicMock()
    service = ReviewService(db)

    db.scalar.return_value = "Book Title"
    assert service._ensure_book_exists("b1") == "Book Title"

    db.scalar.return_value = None
    with pytest.raises(HTTPException) as exc:
        service._ensure_book_exists("missing")
    assert exc.value.status_code == 404


def test_ensure_user_exists_success_and_not_found():
    db = MagicMock()
    service = ReviewService(db)

    db.scalar.return_value = "u1"
    service._ensure_user_exists("u1")

    db.scalar.return_value = None
    with pytest.raises(HTTPException) as exc:
        service._ensure_user_exists("missing")
    assert exc.value.status_code == 404


def test_get_review_or_404_success_and_not_found():
    db = MagicMock()
    service = ReviewService(db)

    review = SimpleNamespace(review_id="r1")
    db.get.return_value = review
    assert service._get_review_or_404("r1") is review

    db.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        service._get_review_or_404("missing")
    assert exc.value.status_code == 404


def test_add_review_maps_comment_sets_title_and_moods():
    db = MagicMock()
    service = ReviewService(db)
    service._ensure_book_exists = MagicMock(return_value="Book Name")
    service._ensure_user_exists = MagicMock(return_value=None)

    payload = _Payload({"rating": 5, "comment": "Great read", "mood": "hopeful"})

    result = service.add_review(book_id="b1", user_id="u1", review_data=payload)

    assert result.body == "Great read"
    assert result.title == "Book Name"
    assert result.comment == "Great read"
    assert result.book_mood == "hopeful"
    assert result.mood == "hopeful"
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_add_review_preserves_existing_title_and_body():
    db = MagicMock()
    service = ReviewService(db)
    service._ensure_book_exists = MagicMock(return_value="Book Name")
    service._ensure_user_exists = MagicMock(return_value=None)

    payload = _Payload(
        {
            "rating": 4,
            "title": "Custom title",
            "body": "Keep this body",
            "comment": "Do not override",
            "book_mood": " calm ",
        }
    )

    result = service.add_review(book_id="b1", user_id="u1", review_data=payload)

    assert result.title == "Custom title"
    assert result.body == "Keep this body"
    assert result.comment == "Keep this body"
    assert result.book_mood == "calm"


def test_add_review_invalid_rating_raises_422():
    db = MagicMock()
    service = ReviewService(db)
    service._ensure_book_exists = MagicMock(return_value="Book Name")
    service._ensure_user_exists = MagicMock(return_value=None)

    payload = _Payload({"rating": 6, "comment": "bad"})

    with pytest.raises(HTTPException) as exc:
        service.add_review(book_id="b1", user_id="u1", review_data=payload)

    assert exc.value.status_code == 422


def test_add_review_integrity_error_maps_to_409():
    db = MagicMock()
    db.commit.side_effect = IntegrityError(None, None, None)
    service = ReviewService(db)
    service._ensure_book_exists = MagicMock(return_value="Book Name")
    service._ensure_user_exists = MagicMock(return_value=None)

    payload = ReviewCreate(rating=5, comment="Great")

    with pytest.raises(HTTPException) as exc:
        service.add_review(book_id="b1", user_id="u1", review_data=payload)

    assert exc.value.status_code == 409
    db.rollback.assert_called_once()


def test_update_review_forbidden_user():
    db = MagicMock()
    service = ReviewService(db)
    service._ensure_user_exists = MagicMock(return_value=None)
    service._get_review_or_404 = MagicMock(return_value=SimpleNamespace(user_id="owner"))

    with pytest.raises(HTTPException) as exc:
        service.update_review("r1", "other", ReviewUpdate(rating=4))

    assert exc.value.status_code == 403


def test_update_review_invalid_rating_raises_422():
    db = MagicMock()
    review = SimpleNamespace(user_id="u1", body="old")
    service = ReviewService(db)
    service._ensure_user_exists = MagicMock(return_value=None)
    service._get_review_or_404 = MagicMock(return_value=review)

    payload = _Payload({"rating": 0})

    with pytest.raises(HTTPException) as exc:
        service.update_review("r1", "u1", payload)

    assert exc.value.status_code == 422


def test_update_review_maps_comment_and_legacy_mood_alias():
    db = MagicMock()
    review = SimpleNamespace(user_id="u1", body="old", rating=3)
    service = ReviewService(db)
    service._ensure_user_exists = MagicMock(return_value=None)
    service._get_review_or_404 = MagicMock(return_value=review)

    payload = _Payload({"comment": "Updated", "mood": "excited", "rating": 5})

    result = service.update_review("r1", "u1", payload)

    assert result.body == "Updated"
    assert result.comment == "Updated"
    assert result.book_mood == "excited"
    assert result.mood == "excited"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(review)


def test_update_review_with_explicit_book_mood_skips_legacy_alias_branch():
    db = MagicMock()
    review = SimpleNamespace(user_id="u1", body="old", rating=3)
    service = ReviewService(db)
    service._ensure_user_exists = MagicMock(return_value=None)
    service._get_review_or_404 = MagicMock(return_value=review)

    payload = _Payload({"comment": "Updated", "book_mood": "focused"})

    result = service.update_review("r1", "u1", payload)

    assert result.book_mood == "focused"
    assert result.mood == "focused"


def test_update_review_with_explicit_body_does_not_use_comment():
    db = MagicMock()
    review = SimpleNamespace(user_id="u1", body="old")
    service = ReviewService(db)
    service._ensure_user_exists = MagicMock(return_value=None)
    service._get_review_or_404 = MagicMock(return_value=review)

    payload = _Payload({"body": "Body wins", "comment": "Ignored"})

    result = service.update_review("r1", "u1", payload)

    assert result.body == "Body wins"
    assert result.comment == "Body wins"


def test_delete_review_success_and_forbidden_paths():
    db = MagicMock()
    service = ReviewService(db)
    service._ensure_user_exists = MagicMock(return_value=None)

    owner_review = SimpleNamespace(user_id="u1")
    service._get_review_or_404 = MagicMock(return_value=owner_review)
    service.delete_review("r1", "u1")
    db.delete.assert_called_once_with(owner_review)
    db.commit.assert_called_once()

    other_review = SimpleNamespace(user_id="owner")
    service._get_review_or_404 = MagicMock(return_value=other_review)
    with pytest.raises(HTTPException) as exc:
        service.delete_review("r1", "other")
    assert exc.value.status_code == 403


def test_get_reviews_by_book_id_sets_comment_and_optional_mood_fields():
    db = MagicMock()
    service = ReviewService(db)
    service._ensure_book_exists = MagicMock(return_value="Book")

    review_without_mood = SimpleNamespace(body="Body 1")
    review_with_mood = SimpleNamespace(body="Body 2", book_mood="serene")
    review_with_existing_mood = SimpleNamespace(body="Body 3", book_mood="calm", mood="already-set")
    db.scalars.return_value.all.return_value = [
        review_without_mood,
        review_with_mood,
        review_with_existing_mood,
    ]

    out = service.get_reviews_by_book_id("b1", limit=5, offset=2, newest_first=False)

    assert len(out) == 3
    assert out[0].comment == "Body 1"
    assert out[0].book_mood is None
    assert out[0].mood is None
    assert out[1].comment == "Body 2"
    assert out[1].mood == "serene"
    assert out[2].comment == "Body 3"
    assert out[2].mood == "already-set"


def test_get_average_rating_returns_value_and_none():
    db = MagicMock()
    service = ReviewService(db)
    service._ensure_book_exists = MagicMock(return_value="Book")

    db.scalar.return_value = 4.236
    assert service.get_average_rating("b1") == 4.24

    db.scalar.return_value = None
    assert service.get_average_rating("b1") is None
