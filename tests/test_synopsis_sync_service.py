from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.models.book import Book
from app.models.synopsis_moderation import SynopsisModeration
from app.services.synopsis_sync_service import SynopsisSyncService


class _FakeQuery:
    def __init__(self, *, all_result=None, first_result=None):
        self._all_result = all_result if all_result is not None else []
        self._first_result = first_result

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self._all_result

    def first(self):
        return self._first_result


def _make_book(book_id: str, title: str, synopsis: str | None = None):
    b = Book(title=title)
    b.book_id = book_id
    b.CommunitySynopsis = synopsis
    return b


def test_init_without_api_key_has_no_client():
    service = SynopsisSyncService(openai_api_key=None)
    assert service.client is None


def test_init_with_api_key_builds_client(monkeypatch):
    fake_client = object()

    def fake_openai(*, api_key):
        assert api_key == "abc"
        return fake_client

    monkeypatch.setattr("app.services.synopsis_sync_service.OpenAI", fake_openai)
    service = SynopsisSyncService(openai_api_key="abc")
    assert service.client is fake_client


def test_get_all_user_reviews_groups_and_filters():
    service = SynopsisSyncService(openai_api_key=None)
    rows = [
        SimpleNamespace(book_id="b1", body="one"),
        SimpleNamespace(book_id="b1", body="two"),
        SimpleNamespace(book_id="b2", body="three"),
    ]

    q = _FakeQuery(all_result=rows)
    db = MagicMock()
    db.query.return_value = q

    out = service.get_all_user_reviews(db, book_id="b1")

    assert out == {"b1": ["one", "two"], "b2": ["three"]}


def test_get_all_user_reviews_raises_on_error():
    service = SynopsisSyncService(openai_api_key=None)
    db = MagicMock()
    db.query.side_effect = RuntimeError("db down")

    with pytest.raises(RuntimeError):
        service.get_all_user_reviews(db)


def test_generate_community_synopsis_without_client_returns_none():
    service = SynopsisSyncService(openai_api_key=None)
    assert service.generate_community_synopsis("Book", ["some long enough text"]) is None


def test_generate_community_synopsis_with_no_valid_reviews_returns_none():
    service = SynopsisSyncService(openai_api_key=None)
    service.client = MagicMock()
    out = service.generate_community_synopsis("Book", ["short", " ", "tiny"])
    assert out is None


def test_generate_community_synopsis_success():
    service = SynopsisSyncService(openai_api_key=None)
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=" Generated summary. "))]
    )
    client = MagicMock()
    client.chat.completions.create.return_value = fake_response
    service.client = client

    out = service.generate_community_synopsis("Book", ["This review text is long enough", "Another long review text"])

    assert out == "Generated summary."


def test_generate_community_synopsis_handles_openai_error():
    service = SynopsisSyncService(openai_api_key=None)
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("openai error")
    service.client = client

    out = service.generate_community_synopsis("Book", ["This review text is long enough"])
    assert out is None


def test_compare_synopses_paths():
    service = SynopsisSyncService(openai_api_key=None)

    assert service.compare_synopses(None, ["x"]) is True
    assert service.compare_synopses("current", []) is False
    assert service.compare_synopses("current", ["12345678901", "abcdefghijk", "zzzzzzzzzzz"]) is True
    assert service.compare_synopses("current", ["12345678901", "abcdefghijk"]) is False


def test_compare_synopses_exception_returns_true():
    service = SynopsisSyncService(openai_api_key=None)
    assert service.compare_synopses("current", [None]) is True


def test_build_user_content_hash_ignores_empty_and_is_deterministic():
    service = SynopsisSyncService(openai_api_key=None)
    h1 = service._build_user_content_hash(["  b  ", "", "a", None])
    h2 = service._build_user_content_hash(["a", "b"])
    assert h1 == h2


def test_upsert_pending_moderation_unchanged():
    service = SynopsisSyncService(openai_api_key=None)
    db = MagicMock()
    pending = SimpleNamespace(
        user_content_hash="h1",
        proposed_synopsis="proposed",
    )
    q = _FakeQuery(first_result=pending)
    db.query.return_value = q

    book = _make_book("b1", "Book", "current")
    result = service._upsert_pending_moderation(
        db,
        book=book,
        proposed_synopsis=" proposed ",
        user_synopsis_count=2,
        user_content_hash="h1",
    )

    assert result == "unchanged"
    db.commit.assert_not_called()


def test_upsert_pending_moderation_updated():
    service = SynopsisSyncService(openai_api_key=None)
    db = MagicMock()
    pending = SimpleNamespace(
        user_content_hash="old",
        proposed_synopsis="old synopsis",
        current_synopsis=None,
        user_synopsis_count=0,
        updated_at=None,
    )
    q = _FakeQuery(first_result=pending)
    db.query.return_value = q

    book = _make_book("b1", "Book", "current")
    result = service._upsert_pending_moderation(
        db,
        book=book,
        proposed_synopsis="new synopsis",
        user_synopsis_count=5,
        user_content_hash="new",
    )

    assert result == "updated"
    assert pending.current_synopsis == "current"
    assert pending.proposed_synopsis == "new synopsis"
    assert pending.user_synopsis_count == 5
    assert pending.user_content_hash == "new"
    db.commit.assert_called_once()


def test_upsert_pending_moderation_created():
    service = SynopsisSyncService(openai_api_key=None)
    db = MagicMock()
    q = _FakeQuery(first_result=None)
    db.query.return_value = q

    book = _make_book("b1", "Book", "current")
    result = service._upsert_pending_moderation(
        db,
        book=book,
        proposed_synopsis="new synopsis",
        user_synopsis_count=1,
        user_content_hash="hash",
    )

    assert result == "created"
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_list_moderation_items_with_and_without_book():
    service = SynopsisSyncService(openai_api_key=None)
    db = MagicMock()

    item1 = SimpleNamespace(
        moderation_id="m1",
        book_id="b1",
        status="pending",
        current_synopsis="c1",
        proposed_synopsis="p1",
        user_synopsis_count=2,
        created_at=None,
        updated_at=None,
        reviewed_at=None,
    )
    item2 = SimpleNamespace(
        moderation_id="m2",
        book_id="b2",
        status="pending",
        current_synopsis="c2",
        proposed_synopsis="p2",
        user_synopsis_count=3,
        created_at=None,
        updated_at=None,
        reviewed_at=None,
    )

    q_items = _FakeQuery(all_result=[item1, item2])
    q_book1 = _FakeQuery(first_result=SimpleNamespace(title="T1"))
    q_book2 = _FakeQuery(first_result=None)
    db.query.side_effect = [q_items, q_book1, q_book2]

    out = service.list_moderation_items(db, status_filter="all")

    assert len(out) == 2
    assert out[0]["book_title"] == "T1"
    assert out[1]["book_title"] == "b2"


def test_list_moderation_items_applies_status_filter_branch():
    service = SynopsisSyncService(openai_api_key=None)
    db = MagicMock()

    item = SimpleNamespace(
        moderation_id="m3",
        book_id="b3",
        status="pending",
        current_synopsis=None,
        proposed_synopsis="p3",
        user_synopsis_count=1,
        created_at=None,
        updated_at=None,
        reviewed_at=None,
    )

    q_items = _FakeQuery(all_result=[item])
    q_book = _FakeQuery(first_result=SimpleNamespace(title="T3"))
    db.query.side_effect = [q_items, q_book]

    out = service.list_moderation_items(db, status_filter="pending")

    assert len(out) == 1
    assert out[0]["book_title"] == "T3"


def test_accept_moderation_item_paths():
    service = SynopsisSyncService(openai_api_key=None)

    db = MagicMock()
    db.query.return_value = _FakeQuery(first_result=None)
    with pytest.raises(ValueError, match="Moderation item not found"):
        service.accept_moderation_item(db, "x")

    db = MagicMock()
    item = SimpleNamespace(status="accepted")
    db.query.side_effect = [_FakeQuery(first_result=item)]
    with pytest.raises(ValueError, match="Only pending items can be accepted"):
        service.accept_moderation_item(db, "x")

    db = MagicMock()
    item = SimpleNamespace(status="pending", item_id="x", book_id="b1")
    db.query.side_effect = [_FakeQuery(first_result=item), _FakeQuery(first_result=None)]
    with pytest.raises(ValueError, match="Book not found for moderation item"):
        service.accept_moderation_item(db, "x")

    db = MagicMock()
    item = SimpleNamespace(moderation_id="m1", status="pending", proposed_synopsis="new", book_id="b1")
    book = _make_book("b1", "Title", "old")
    db.query.side_effect = [_FakeQuery(first_result=item), _FakeQuery(first_result=book)]

    out = service.accept_moderation_item(db, "m1")

    assert out["status"] == "accepted"
    assert out["book_title"] == "Title"
    assert out["community_synopsis"] == "new"
    db.commit.assert_called_once()


def test_reject_moderation_item_paths():
    service = SynopsisSyncService(openai_api_key=None)

    db = MagicMock()
    db.query.return_value = _FakeQuery(first_result=None)
    with pytest.raises(ValueError, match="Moderation item not found"):
        service.reject_moderation_item(db, "x")

    db = MagicMock()
    item = SimpleNamespace(status="accepted")
    db.query.side_effect = [_FakeQuery(first_result=item)]
    with pytest.raises(ValueError, match="Only pending items can be rejected"):
        service.reject_moderation_item(db, "x")

    db = MagicMock()
    item = SimpleNamespace(moderation_id="m2", book_id="b2", status="pending")
    db.query.side_effect = [_FakeQuery(first_result=item)]
    out = service.reject_moderation_item(db, "m2")

    assert out["status"] == "rejected"
    db.commit.assert_called_once()


def test_generate_all_community_reviews_no_reviews():
    service = SynopsisSyncService(openai_api_key=None)
    db = MagicMock()
    service.get_all_user_reviews = MagicMock(return_value={})

    out = service.generate_all_community_reviews(db)

    assert out["status"] == "success"
    assert out["total_books_processed"] == 0
    assert out["proposed"] == 0
    assert out["refreshed"] == 0


def test_generate_all_community_reviews_mixed_paths():
    service = SynopsisSyncService(openai_api_key=None)
    db = MagicMock()

    user_map = {
        "created": ["review text one long enough"],
        "updated": ["review text two long enough"],
        "unchanged": ["review text three long enough"],
        "same": ["same synopsis text"],
        "none": ["none synopsis text"],
        "skip": ["skip text"],
        "missing": ["missing book"],
        "error": ["error text"],
    }
    service.get_all_user_reviews = MagicMock(return_value=user_map)

    books = [
        _make_book("created", "Created", "old"),
        _make_book("updated", "Updated", "old"),
        _make_book("unchanged", "Unchanged", "old"),
        _make_book("same", "Same", "same synopsis text"),
        _make_book("none", "None", "old"),
        _make_book("skip", "Skip", "old"),
        None,
        _make_book("error", "Error", "old"),
    ]
    q_books = _FakeQuery()
    q_books.first = MagicMock(side_effect=books)
    db.query.return_value = q_books

    def compare_side_effect(current, synopses):
        return synopses != ["skip text"]

    service.compare_synopses = MagicMock(side_effect=compare_side_effect)

    def generate_side_effect(title, synopses):
        if synopses == ["same synopsis text"]:
            return "same synopsis text"
        if synopses == ["none synopsis text"]:
            return None
        if synopses == ["error text"]:
            raise RuntimeError("boom")
        return f"generated-{title}"

    service.generate_community_synopsis = MagicMock(side_effect=generate_side_effect)

    def upsert_side_effect(db_obj, *, book, proposed_synopsis, user_synopsis_count, user_content_hash):
        if book.book_id == "created":
            return "created"
        if book.book_id == "updated":
            return "updated"
        return "unchanged"

    service._upsert_pending_moderation = MagicMock(side_effect=upsert_side_effect)

    out = service.generate_all_community_reviews(db)

    assert out["status"] == "success"
    assert out["total_books_processed"] == len(user_map)
    assert out["proposed"] == 1
    assert out["refreshed"] == 1
    assert out["skipped"] == 5
    assert len(out["errors"]) == 1
    db.rollback.assert_called_once()


def test_generate_all_community_reviews_outer_exception():
    service = SynopsisSyncService(openai_api_key=None)
    db = MagicMock()
    service.get_all_user_reviews = MagicMock(side_effect=RuntimeError("critical"))

    out = service.generate_all_community_reviews(db)

    assert out["status"] == "error"
    assert out["message"] == "critical"
    assert out["total_books_processed"] == 0


def test_sync_all_synopses_alias_calls_generate():
    service = SynopsisSyncService(openai_api_key=None)
    db = MagicMock()
    service.generate_all_community_reviews = MagicMock(return_value={"status": "ok"})

    out = service.sync_all_synopses(db)

    assert out == {"status": "ok"}
    service.generate_all_community_reviews.assert_called_once_with(db)
