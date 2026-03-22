from datetime import date, datetime, timedelta
import json

import pytest

from app.models.book import Book
from app.models.bookshelf import Bookshelf
from app.services import bookshelf_service as bs_mod
from app.services.bookshelf_service import BookshelfService, _validate_transition


@pytest.fixture
def seeded_book(db):
    book = Book(book_id="book-1", title="Book One")
    db.add(book)
    db.commit()
    return book


def _add_item(db, user_id="u1", book_id="book-1", status="want_to_read"):
    now = datetime.utcnow()
    item = Bookshelf(
        user_id=user_id,
        book_id=book_id,
        shelf_status=status,
        date_added=now,
        updated_at=now,
    )
    db.add(item)
    db.commit()
    return item


def test_validate_transition_paths():
    _validate_transition("want_to_read", "currently_reading")

    with pytest.raises(ValueError, match="Invalid shelf_status"):
        _validate_transition("want_to_read", "invalid")

    with pytest.raises(ValueError, match="Cannot move status backwards"):
        _validate_transition("read", "want_to_read")


def test_add_to_shelf_not_found(db):
    svc = BookshelfService(db)

    with pytest.raises(ValueError, match="Book not found"):
        svc.add_to_shelf(user_id="u1", book_id="missing")


def test_add_to_shelf_and_duplicate(db, seeded_book):
    svc = BookshelfService(db)

    created = svc.add_to_shelf(user_id="u1", book_id=seeded_book.book_id)
    assert created.shelf_status == "want_to_read"

    with pytest.raises(ValueError, match="DUPLICATE"):
        svc.add_to_shelf(user_id="u1", book_id=seeded_book.book_id)


def test_remove_from_shelf_paths(db, seeded_book):
    svc = BookshelfService(db)

    with pytest.raises(ValueError, match="NOT_FOUND"):
        svc.remove_from_shelf(user_id="u1", book_id=seeded_book.book_id)

    _add_item(db, book_id=seeded_book.book_id)
    svc.remove_from_shelf(user_id="u1", book_id=seeded_book.book_id)
    remaining = db.query(Bookshelf).filter_by(user_id="u1", book_id=seeded_book.book_id).first()
    assert remaining is None


def test_update_status_paths(db, seeded_book):
    svc = BookshelfService(db)

    with pytest.raises(ValueError, match="NOT_FOUND"):
        svc.update_status(user_id="u1", book_id=seeded_book.book_id, new_status="read")

    item = _add_item(db, user_id="u1", book_id=seeded_book.book_id, status="want_to_read")

    first = svc.update_status(user_id="u1", book_id=seeded_book.book_id, new_status="currently_reading")
    assert first.date_started is not None
    started_at = first.date_started

    second = svc.update_status(user_id="u1", book_id=seeded_book.book_id, new_status="currently_reading")
    assert second.date_started == started_at

    third = svc.update_status(user_id="u1", book_id=seeded_book.book_id, new_status="read")
    assert third.date_started is not None
    assert third.date_finished is not None

    item.date_started = None
    item.date_finished = datetime.utcnow() - timedelta(days=2)
    db.commit()

    with pytest.raises(ValueError, match="Invalid dates: finished before started"):
        svc.update_status(user_id="u1", book_id=seeded_book.book_id, new_status="read")


def test_update_progress_paths(db, seeded_book):
    svc = BookshelfService(db)

    with pytest.raises(ValueError, match="NOT_FOUND"):
        svc.update_progress(user_id="u1", book_id=seeded_book.book_id, progress_percent=10)

    item = _add_item(db, user_id="u1", book_id=seeded_book.book_id, status="want_to_read")
    with pytest.raises(ValueError, match="Progress can only be updated"):
        svc.update_progress(user_id="u1", book_id=seeded_book.book_id, progress_percent=20)

    item.shelf_status = "currently_reading"
    item.synopsis = "[]"
    db.commit()

    updated = svc.update_progress(
        user_id="u1",
        book_id=seeded_book.book_id,
        progress_percent=45,
        book_moods=["Happy", " happy ", "Calm"],
    )
    payload = json.loads(updated.synopsis)
    assert payload["progress_percent"] == 45
    assert payload["book_moods"] == ["Happy", "Calm"]
    assert payload["book_mood"] == "Happy, Calm"
    assert payload["moods"] == ["Happy", "Calm"]
    assert payload["mood"] == "Happy, Calm"
    assert payload["last_check_in_at"]

    updated2 = svc.update_progress(
        user_id="u1",
        book_id=seeded_book.book_id,
        progress_percent=50,
        mood=" cozy, reflective ,, ",
    )
    payload2 = json.loads(updated2.synopsis)
    assert payload2["book_moods"] == ["cozy", "reflective"]
    assert payload2["book_mood"] == "cozy, reflective"


def test_list_timeline_stats(db, seeded_book, monkeypatch):
    svc = BookshelfService(db)

    fixed_now = datetime(2026, 3, 22, 12, 0, 0)
    monkeypatch.setattr(bs_mod, "_now", lambda: fixed_now)

    _add_item(db, user_id="u1", book_id=seeded_book.book_id, status="want_to_read")
    b2 = Book(book_id="book-2", title="Book Two")
    b3 = Book(book_id="book-3", title="Book Three")
    db.add_all([b2, b3])
    db.commit()

    i2 = _add_item(db, user_id="u1", book_id="book-2", status="read")
    i2.date_added = fixed_now - timedelta(days=12)
    i2.date_started = fixed_now - timedelta(days=10)
    i2.date_finished = fixed_now - timedelta(days=2)

    i3 = _add_item(db, user_id="u1", book_id="book-3", status="read")
    i3.date_added = fixed_now - timedelta(days=9)
    i3.date_started = fixed_now - timedelta(days=8)
    i3.date_finished = fixed_now - timedelta(days=1)
    db.commit()

    listed = svc.list_shelf(user_id="u1", sort="unknown", order="asc")
    assert len(listed) == 3

    filtered = svc.list_shelf(user_id="u1", status="read", sort="date_finished", order="desc")
    assert [x.book_id for x in filtered] == ["book-3", "book-2"]

    timeline = svc.get_timeline(user_id="u1")
    assert [x.book_id for x in timeline][:2] == ["book-3", "book-2"]

    stats = svc.get_stats(user_id="u1")
    assert stats["read_this_month"] == 2
    assert stats["read_this_year"] == 2
    assert stats["avg_days_to_finish"] == 7.5
    assert stats["best_streak_days"] == 2
    assert stats["current_streak_days"] == 2

    empty_stats = svc.get_stats(user_id="nobody")
    assert empty_stats["read_this_month"] == 0
    assert empty_stats["read_this_year"] == 0
    assert empty_stats["avg_days_to_finish"] is None
    assert empty_stats["best_streak_days"] == 0
    assert empty_stats["current_streak_days"] == 0
