from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.user import User
from app.routes import review as review_routes
from app.routes.review import resolve_user_id


def test_resolve_user_id_happy_path_dict_id(db):
    assert resolve_user_id({"id": "u1"}, db) == "u1"


def test_resolve_user_id_missing_sub_raises(db):
    with pytest.raises(HTTPException) as exc:
        resolve_user_id({"email": "x@test.com"}, db)
    assert exc.value.status_code == 401


def test_resolve_user_id_sub_not_found_raises(db):
    with pytest.raises(HTTPException) as exc:
        resolve_user_id({"sub": "unknown-sub"}, db)
    assert exc.value.status_code == 401


def test_resolve_user_id_sub_found(db):
    user = User(email="route@test.com", cognito_sub="route-sub")
    db.add(user)
    db.commit()

    uid = resolve_user_id({"sub": "route-sub"}, db)
    assert uid == str(user.user_id)


def test_review_get_review_direct_path():
    review_obj = SimpleNamespace(
        review_id="r-1",
        book_id="b-1",
        user_id="u-1",
        rating=5,
        title="Great",
        body="Excellent",
        comment=None,
        book_mood=None,
        mood="happy",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    service = MagicMock()
    service._get_review_or_404.return_value = review_obj

    out = review_routes.get_review("r-1", service)
    assert out.review_id == "r-1"
    assert out.comment == "Excellent"
    assert out.book_mood == "happy"


def test_review_schema_from_orm_alias_branches():
    from app.schemas.review import ReviewOut

    review_obj = SimpleNamespace(
        review_id="r-2",
        book_id="b-2",
        user_id="u-2",
        rating=4,
        title="Solid",
        body="Body text",
        comment=None,
        book_mood=None,
        mood="curious",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    out = ReviewOut.from_orm_with_comment(review_obj)
    assert out.comment == "Body text"
    assert out.book_mood == "curious"
