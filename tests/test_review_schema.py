from datetime import datetime
from types import SimpleNamespace

from app.schemas.review import ReviewOut


def test_from_orm_with_comment_maps_body_and_mood_aliases():
    review_obj = SimpleNamespace(
        review_id="review-1",
        book_id="book-1",
        user_id="user-1",
        rating=5,
        title="Title",
        body="Body text",
        comment=None,
        book_mood=None,
        mood="inspired",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    out = ReviewOut.from_orm_with_comment(review_obj)

    assert out.comment == "Body text"
    assert out.book_mood == "inspired"
