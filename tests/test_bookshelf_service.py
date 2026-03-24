import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, call
from sqlalchemy.orm import Session

from app.services.bookshelf_service import (
    BookshelfService,
    _validate_transition,
    _now,
    STATUS_ORDER,
)
from app.models.bookshelf import Bookshelf
from app.models.book import Book

# Helper functions for tests
def make_shelf(**kwargs):
    defaults = dict(
        user_id="user-1",
        book_id="book-1",
        shelf_status="want_to_read",
        date_added=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
        date_started=None,
        date_finished=None,
        synopsis=None,
    )
    defaults.update(kwargs)
    return Bookshelf(**defaults)

def mock_scalar(value):
    """Return a mock that behaves like execute().scalar_one_or_none()"""
    m = MagicMock()
    m.scalar_one_or_none.return_value = value
    return m

def mock_scalars(values):
    """Return a mock that behaves like execute().scalars().all()"""
    m = MagicMock()
    m.scalars.return_value.all.return_value = values
    return m

# Test valid forward status transitions do not raise any exceptions
def test_validate_transition_valid_forward():
    _validate_transition("want_to_read", "currently_reading")
    _validate_transition("currently_reading", "read")
    _validate_transition("want_to_read", "read")

# Test passing an unrecongised status raises a ValueError
def test_validate_transition_invalid_status():
    with pytest.raises(ValueError, match="Invalid shelf_status"):
        _validate_transition("want_to_read", "invalid_status")

# Test moving status backwards raises a ValueError
def test_validate_transition_backwards():
    with pytest.raises(ValueError, match="Cannot move status backwards"):
        _validate_transition("read", "want_to_read")
    with pytest.raises(ValueError, match="Cannot move status backwards"):
        _validate_transition("currently_reading", "want_to_read")

 
class TestAddToShelf:

    def setup_method(self):
        self.db = MagicMock(spec=Session)
        self.service = BookshelfService(db=self.db)

    # Test when a book is added to the shelf with "want_to_read" status when book exists and no duplicate entry.
    def test_add_to_shelf_success(self):
        item = make_shelf()
        self.db.execute.side_effect = [
            mock_scalar("book-1"),   # book exists check
            mock_scalar(None),       # no existing shelf entry
        ]
        self.db.refresh.side_effect = lambda x: x

        result = self.service.add_to_shelf(user_id="user-1", book_id="book-1")

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        assert result.shelf_status == "want_to_read"

    # Test adding a book that does not exist raises a ValueError with "Book not found" message.
    def test_add_to_shelf_book_not_found(self):
        self.db.execute.return_value = mock_scalar(None)
        with pytest.raises(ValueError, match="Book not found"):
            self.service.add_to_shelf(user_id="user-1", book_id="bad-book")

    # Test adding a book that is already on the bookshelf raises a ValueError with "DUPLICATE" message.
    def test_add_to_shelf_duplicate(self):
        existing = make_shelf()
        self.db.execute.side_effect = [
            mock_scalar("book-1"),
            mock_scalar(existing),
        ]
        with pytest.raises(ValueError, match="DUPLICATE"):
            self.service.add_to_shelf(user_id="user-1", book_id="book-1")


class TestRemoveFromShelf:

    def setup_method(self):
        self.db = MagicMock(spec=Session)
        self.service = BookshelfService(db=self.db)

    # Test removing a book from the shelf successfully deletes the item and commits the transaction.
    def test_remove_success(self):
        item = make_shelf()
        self.db.execute.return_value = mock_scalar(item)

        self.service.remove_from_shelf(user_id="user-1", book_id="book-1")

        self.db.delete.assert_called_once_with(item)
        self.db.commit.assert_called_once()
    
    # Test trying to remove a book that is not on the shelf raises a ValueError with "NOT_FOUND" message.
    def test_remove_not_found(self):
        self.db.execute.return_value = mock_scalar(None)
        with pytest.raises(ValueError, match="NOT_FOUND"):
            self.service.remove_from_shelf(user_id="user-1", book_id="book-1")

class TestUpdateStatus:

    def setup_method(self):
        self.db = MagicMock(spec=Session)
        self.service = BookshelfService(db=self.db)

    # Test updating the status of a book that is not on the shelf raises a ValueError with "NOT_FOUND" message.
    def test_update_status_not_found(self):
        self.db.execute.return_value = mock_scalar(None)
        with pytest.raises(ValueError, match="NOT_FOUND"):
            self.service.update_status(user_id="user-1", book_id="book-1", new_status="currently_reading")

    # Test valid status transition updates the shelf_status and updated_at fields and commits the transaction.
    def test_update_status_to_currently_reading_sets_date_started(self):
        item = make_shelf(shelf_status="want_to_read")
        self.db.execute.return_value = mock_scalar(item)
        self.db.refresh.side_effect = lambda x: x

        self.service.update_status(user_id="user-1", book_id="book-1", new_status="currently_reading")

        assert item.date_started is not None
        assert item.shelf_status == "currently_reading"

    # Test updating to currently_reading does not overwrite existing date_started
    def test_update_status_currently_reading_does_not_overwrite_date_started(self):
        original_start = datetime(2024, 3, 1)
        item = make_shelf(shelf_status="want_to_read", date_started=original_start)
        self.db.execute.return_value = mock_scalar(item)
        self.db.refresh.side_effect = lambda x: x

        self.service.update_status(user_id="user-1", book_id="book-1", new_status="currently_reading")

        assert item.date_started == original_start
    
    # Test updating to read sets date_started and date_finished
    def test_update_status_to_read_sets_dates(self):
        item = make_shelf(shelf_status="currently_reading")
        self.db.execute.return_value = mock_scalar(item)
        self.db.refresh.side_effect = lambda x: x

        self.service.update_status(user_id="user-1", book_id="book-1", new_status="read")

        assert item.date_started is not None
        assert item.date_finished is not None

    #  Test updating to read does not overwrite existing date_started and date_finished
    def test_update_status_to_read_does_not_overwrite_existing_dates(self):
        start = datetime(2024, 1, 1)
        finish = datetime(2024, 2, 1)
        item = make_shelf(shelf_status="currently_reading", date_started=start, date_finished=finish)
        self.db.execute.return_value = mock_scalar(item)
        self.db.refresh.side_effect = lambda x: x

        self.service.update_status(user_id="user-1", book_id="book-1", new_status="read")

        assert item.date_started == start
        assert item.date_finished == finish
    
    # Test updating to read with date_finished before date_started raises a ValueError with "Invalid dates" message.
    def test_update_status_invalid_dates_raises(self):
        # date_finished before date_started
        item = make_shelf(
            shelf_status="currently_reading",
            date_started=datetime(2024, 5, 1),
            date_finished=datetime(2024, 1, 1),
        )
        self.db.execute.return_value = mock_scalar(item)

        with pytest.raises(ValueError, match="Invalid dates"):
            self.service.update_status(user_id="user-1", book_id="book-1", new_status="read")


class TestUpdateProgress:

    def setup_method(self):
        self.db = MagicMock(spec=Session)
        self.service = BookshelfService(db=self.db)

    # Test updating the progress of a book that is not on the shelf raises a ValueError with "NOT_FOUND" message.
    def test_update_progress_not_found(self):
        self.db.execute.return_value = mock_scalar(None)
        with pytest.raises(ValueError, match="NOT_FOUND"):
            self.service.update_progress(user_id="user-1", book_id="book-1", progress_percent=50)

    # Test updating the progress of a book that is not currently_reading raises a ValueError with "Progress can only be updated" message.
    def test_update_progress_invalid_status(self):
        item = make_shelf(shelf_status="want_to_read")
        self.db.execute.return_value = mock_scalar(item)
        with pytest.raises(ValueError, match="Progress can only be updated"):
            self.service.update_progress(user_id="user-1", book_id="book-1", progress_percent=50)

    # Test updating the progress of a book that is currently_reading updates the progress_percent and mood fields.
    def test_update_progress_success_with_mood(self):
        item = make_shelf(shelf_status="currently_reading")
        self.db.execute.return_value = mock_scalar(item)
        self.db.refresh.side_effect = lambda x: x

        self.service.update_progress(
            user_id="user-1", book_id="book-1",
            progress_percent=60, mood="happy"
        )

        payload = json.loads(item.synopsis)
        assert payload["progress_percent"] == 60
        assert payload["mood"] == "happy"

    # Test updating the progress with a list of moods deduplicates and stores them as book_moods
    def test_update_progress_with_moods_list(self):
        item = make_shelf(shelf_status="currently_reading")
        self.db.execute.return_value = mock_scalar(item)
        self.db.refresh.side_effect = lambda x: x

        self.service.update_progress(
            user_id="user-1", book_id="book-1",
            progress_percent=40, moods=["happy", "excited", "happy"]  # duplicate
        )

        payload = json.loads(item.synopsis)
        assert payload["book_moods"] == ["happy", "excited"]  # deduped

    # Test updating the progress with both moods and book_moods prioritises book_moods in the stored synopsis
    def test_update_progress_with_book_moods_overrides_moods(self):
        item = make_shelf(shelf_status="currently_reading")
        self.db.execute.return_value = mock_scalar(item)
        self.db.refresh.side_effect = lambda x: x

        self.service.update_progress(
            user_id="user-1", book_id="book-1",
            progress_percent=50, moods=["sad"], book_moods=["joyful"]
        )

        payload = json.loads(item.synopsis)
        assert payload["book_moods"] == ["joyful"]

    # Test updating the progress with a comma-separated string in book_mood splits and stores them as book_moods
    def test_update_progress_with_book_mood_string(self):
        item = make_shelf(shelf_status="currently_reading")
        self.db.execute.return_value = mock_scalar(item)
        self.db.refresh.side_effect = lambda x: x

        self.service.update_progress(
            user_id="user-1", book_id="book-1",
            progress_percent=30, book_mood="calm, reflective"
        )

        payload = json.loads(item.synopsis)
        assert payload["book_moods"] == ["calm", "reflective"]

    # Test updating the progress preserves existing data in the synopsis JSON if it is valid JSON
    def test_update_progress_existing_synopsis_parsed(self):
        existing = {"some_key": "some_value"}
        item = make_shelf(shelf_status="currently_reading", synopsis=json.dumps(existing))
        self.db.execute.return_value = mock_scalar(item)
        self.db.refresh.side_effect = lambda x: x

        self.service.update_progress(user_id="user-1", book_id="book-1", progress_percent=70)

        payload = json.loads(item.synopsis)
        assert payload["some_key"] == "some_value"  # existing data preserved
        assert payload["progress_percent"] == 70

    # Test updating the progress with invalid JSON in the existing synopsis resets it to a new JSON with just the progress_percent
    def test_update_progress_invalid_synopsis_json_resets(self):
        item = make_shelf(shelf_status="currently_reading", synopsis="not-valid-json")
        self.db.execute.return_value = mock_scalar(item)
        self.db.refresh.side_effect = lambda x: x

        self.service.update_progress(user_id="user-1", book_id="book-1", progress_percent=20)

        payload = json.loads(item.synopsis)
        assert payload["progress_percent"] == 20

    # Test updating the progress when synopsis is not a JSON string resets it to a new JSON with just the progress_percent
    def test_update_progress_non_dict_synopsis_resets(self):
        item = make_shelf(shelf_status="currently_reading", synopsis=json.dumps([1, 2, 3]))
        self.db.execute.return_value = mock_scalar(item)
        self.db.refresh.side_effect = lambda x: x

        self.service.update_progress(user_id="user-1", book_id="book-1", progress_percent=10)

        payload = json.loads(item.synopsis)
        assert payload["progress_percent"] == 10


class TestListShelf:

    def setup_method(self):
        self.db = MagicMock(spec=Session)
        self.service = BookshelfService(db=self.db)

    # Test listing the shelf with no filters returns all items for the user.
    def test_list_shelf_no_filter(self):
        items = [make_shelf(), make_shelf(book_id="book-2")]
        self.db.execute.return_value = mock_scalars(items)

        result = self.service.list_shelf(user_id="user-1")
        assert len(result) == 2

    # Test listing the shelf with a status filter returns only items with that status.
    def test_list_shelf_with_status_filter(self):
        items = [make_shelf(shelf_status="read")]
        self.db.execute.return_value = mock_scalars(items)

        result = self.service.list_shelf(user_id="user-1", status="read")
        assert result[0].shelf_status == "read"

    # Test listing the shelf with sort by date_added orders the results by the date_added field.
    def test_list_shelf_sort_by_date_added(self):
        self.db.execute.return_value = mock_scalars([])
        self.service.list_shelf(user_id="user-1", sort="date_added", order="asc")
        self.db.execute.assert_called_once()

    # Test listing the shelf with sort by updated_at orders the results by the updated_at field.
    def test_list_shelf_unknown_sort_falls_back(self):
        self.db.execute.return_value = mock_scalars([])
        self.service.list_shelf(user_id="user-1", sort="nonexistent_col")
        self.db.execute.assert_called_once()


class TestGetTimeline:

    def setup_method(self):
        self.db = MagicMock(spec=Session)
        self.service = BookshelfService(db=self.db)

    # Test fetching the timeline returns items that have either date_started or date_finished set, ordered by date_finished desc, then date_started desc, then updated_at desc.
    def test_get_timeline_returns_items_with_dates(self):
        now = datetime(2024, 6, 1)
        item = make_shelf(date_started=now, date_finished=now)
        self.db.execute.return_value = mock_scalars([item])

        result = self.service.get_timeline(user_id="user-1")
        assert len(result) == 1

    # Test fetching the timeline does not return items that have neither date_started nor date_finished set.
    def test_get_timeline_empty(self):
        self.db.execute.return_value = mock_scalars([])
        result = self.service.get_timeline(user_id="user-1")
        assert result == []


class TestGetStats:

    def setup_method(self):
        self.db = MagicMock(spec=Session)
        self.service = BookshelfService(db=self.db)

    # Test fetching stats with no read books returns zeros and None for averages.
    def _make_read_item(self, date_started, date_finished):
        return make_shelf(
            shelf_status="read",
            date_started=date_started,
            date_finished=date_finished,
        )
    
    # Test fetching stats with no read books returns zeros and None for averages.
    def test_get_stats_empty(self):
        self.db.execute.return_value = mock_scalars([])
        result = self.service.get_stats(user_id="user-1")
        assert result["read_this_month"] == 0
        assert result["read_this_year"] == 0
        assert result["avg_days_to_finish"] is None
        assert result["current_streak_days"] == 0
        assert result["best_streak_days"] == 0

    # Test fetching stats counts books read this year and this month based on date_finished
    def test_get_stats_counts_this_year_and_month(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        item = self._make_read_item(
            date_started=datetime(now.year, now.month, 1),
            date_finished=datetime(now.year, now.month, 15),
        )
        self.db.execute.return_value = mock_scalars([item])

        result = self.service.get_stats(user_id="user-1")
        assert result["read_this_year"] == 1
        assert result["read_this_month"] == 1

    #  Test fetching stats with a book finished in a previous month/year does not count towards this month/year totals
    def test_get_stats_avg_days_calculated(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        item = self._make_read_item(
            date_started=datetime(now.year, now.month, 1),
            date_finished=datetime(now.year, now.month, 11),
        )
        self.db.execute.return_value = mock_scalars([item])

        result = self.service.get_stats(user_id="user-1")
        assert result["avg_days_to_finish"] == pytest.approx(10.0, abs=0.1)

    #Test fetching stats skips items that have no date_finished when calculating averages and streaks
    def test_get_stats_skips_item_with_no_date_finished(self):
        item = make_shelf(shelf_status="read", date_started=datetime(2024, 1, 1), date_finished=None)
        self.db.execute.return_value = mock_scalars([item])

        result = self.service.get_stats(user_id="user-1")
        assert result["avg_days_to_finish"] is None

    #Test fetching stats uses date_added as fallback when no date_started for calculating avg_days_to_finish
    def test_get_stats_uses_date_added_when_no_date_started(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        item = make_shelf(
            shelf_status="read",
            date_added=datetime(now.year, now.month, 1),
            date_started=None,
            date_finished=datetime(now.year, now.month, 6),
        )
        self.db.execute.return_value = mock_scalars([item])

        result = self.service.get_stats(user_id="user-1")
        assert result["avg_days_to_finish"] == pytest.approx(5.0, abs=0.1)

    # Test fetching stats with multiple books calculates the best streak of consecutive days reading correctly
    def test_get_stats_streak_consecutive_days(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        today = now.date()
        items = [
            self._make_read_item(
                date_started=datetime(today.year, today.month, today.day) - timedelta(days=i+1),
                date_finished=datetime(today.year, today.month, today.day) - timedelta(days=i),
            )
            for i in range(3)
        ]
        self.db.execute.return_value = mock_scalars(items)

        result = self.service.get_stats(user_id="user-1")
        assert result["best_streak_days"] >= 3
    # Test fetching stats with a book finished before it was started is excluded from average days to finish calculation
    def test_get_stats_finished_before_started_excluded_from_avg(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        item = self._make_read_item(
            date_started=datetime(now.year, now.month, 10),
            date_finished=datetime(now.year, now.month, 5),  # before start
        )
        self.db.execute.return_value = mock_scalars([item])

        result = self.service.get_stats(user_id="user-1")
        assert result["avg_days_to_finish"] is None  # excluded from avg

    # Test fetching stats with a book finished today counts towards the current streak
    def test_get_stats_current_streak_today(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        item = self._make_read_item(
            date_started=datetime(now.year, now.month, now.day),
            date_finished=datetime(now.year, now.month, now.day),
        )
        self.db.execute.return_value = mock_scalars([item])

        result = self.service.get_stats(user_id="user-1")
        assert result["current_streak_days"] >= 1