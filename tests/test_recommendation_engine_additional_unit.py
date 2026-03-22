import json
from datetime import date
from types import SimpleNamespace

import pytest

from app.models.book import Book
from app.models.mood import Mood
from app.services.mood_recommendation.recommendation_engine import RecommendationEngine


class _BookService:
    def __init__(self, books):
        self._books = {b.book_id: b for b in books}

    def get_books(self):
        return list(self._books.values())

    def get_book(self, book_id):
        return self._books.get(book_id)


class _ReviewService:
    def __init__(self, reviews_by_book=None, avg_by_book=None, db=None):
        self._reviews_by_book = reviews_by_book or {}
        self._avg_by_book = avg_by_book or {}
        self.db = db

    def get_reviews_by_book_id(self, book_id, **kwargs):
        return self._reviews_by_book.get(book_id, [])

    def get_average_rating(self, book_id):
        return self._avg_by_book.get(book_id)


class _BookshelfService:
    def __init__(self, read_ids=None):
        self._read_ids = set(read_ids or [])

    def list_shelf(self, user_id=None, status="read", **kwargs):
        return [SimpleNamespace(book_id=bid) for bid in self._read_ids]


class _Extractor:
    def __init__(self, scores):
        self._scores = scores

    def extract_emotions(self, text):
        return {"scores": dict(self._scores)}


class _Profiler:
    def __init__(self, scores_by_book):
        self._scores_by_book = scores_by_book

    def create_book_profile(self, book_id, book_title, reviews):
        return {
            "title": book_title,
            "num_reviews": len(reviews),
            "emotion_scores": dict(self._scores_by_book.get(book_id, {})),
            "emotion_counts": {},
        }


def _make_engine(
    *,
    books,
    reviews_by_book=None,
    avg_by_book=None,
    read_ids=None,
    review_scores=None,
    profile_scores_by_book=None,
    db=None,
    review_service_db=None,
):
    return RecommendationEngine(
        book_service=_BookService(books),
        review_service=_ReviewService(reviews_by_book=reviews_by_book, avg_by_book=avg_by_book, db=review_service_db),
        bookshelf_service=_BookshelfService(read_ids=read_ids),
        db=db,
        emotion_extractor_instance=_Extractor(review_scores or {}),
        emotion_profiler_instance=_Profiler(profile_scores_by_book or {}),
    )


def test_get_user_moods_requires_db_when_not_configured():
    engine = _make_engine(books=[])
    with pytest.raises(NotImplementedError, match="Database session not configured"):
        engine.get_user_moods("u1")


def test_get_user_moods_with_db_returns_entries(db):
    db.add(Mood(user_id="u1", mood="happy", mood_date=date(2026, 3, 22)))
    db.add(Mood(user_id="u1", mood="sad", mood_date=date(2026, 3, 21)))
    db.commit()

    engine = _make_engine(books=[], db=db)
    moods = engine.get_user_moods("u1")
    assert len(moods) == 2


def test_init_uses_default_emotion_dependencies(monkeypatch):
    import app.services.mood_recommendation.emotion_extractor as ee
    import app.services.mood_recommendation.emotion_profiler as ep

    fake_extractor = SimpleNamespace(name="extractor")
    fake_profiler = SimpleNamespace(name="profiler")

    monkeypatch.setattr(ee, "emotion_extractor", fake_extractor)
    monkeypatch.setattr(ep, "get_book_profiler", lambda extractor: fake_profiler if extractor is fake_extractor else None)

    engine = RecommendationEngine(
        book_service=_BookService([]),
        review_service=_ReviewService(),
        bookshelf_service=_BookshelfService(),
    )

    assert engine.emotion_extractor is fake_extractor
    assert engine.emotion_profiler is fake_profiler


def test_get_emotion_profile_loads_saved_profile_from_db(db):
    book = Book(book_id="b1", title="Book One", emotion_profile=json.dumps({"happy": {"score": 80, "count": 4}}))
    db.add(book)
    db.commit()

    engine = _make_engine(books=[book], db=db)
    profile = engine.get_emotion_profile("b1", "Book One", ["x", "y"])

    assert profile["emotion_scores"] == {"happy": 80}
    assert profile["emotion_counts"] == {"happy": 4}


def test_get_emotion_profile_falls_back_when_saved_profile_invalid(db):
    book = Book(book_id="b2", title="Book Two", emotion_profile="{invalid json")
    db.add(book)
    db.commit()

    engine = _make_engine(
        books=[book],
        db=db,
        profile_scores_by_book={"b2": {"sad": 55.0}},
    )

    profile = engine.get_emotion_profile("b2", "Book Two", ["review"])
    assert profile["emotion_scores"] == {"sad": 55.0}


def test_get_emotion_profile_falls_back_on_db_error(monkeypatch):
    class _BrokenDB:
        def query(self, *args, **kwargs):
            raise RuntimeError("db error")

    book = SimpleNamespace(book_id="b3", title="Book Three")
    engine = _make_engine(
        books=[book],
        db=_BrokenDB(),
        profile_scores_by_book={"b3": {"joy": 40.0}},
    )

    profile = engine.get_emotion_profile("b3", "Book Three", ["review"])
    assert profile["emotion_scores"] == {"joy": 40.0}


def test_recommend_content_based_target_missing_returns_empty():
    engine = _make_engine(books=[], read_ids=set())
    assert engine.recommend_content_based("u1", "missing", 5, "great") == []


def test_recommend_content_based_unhandled_rating_returns_empty():
    b1 = SimpleNamespace(book_id="b1", title="Target")
    engine = _make_engine(
        books=[b1],
        reviews_by_book={"b1": [SimpleNamespace(body="x")]},
        profile_scores_by_book={"b1": {"happy": 100}},
        review_scores={"happy": 100},
    )
    assert engine.recommend_content_based("u1", "b1", 99, "text") == []


def test_recommend_content_based_empty_results_for_each_rating_mode():
    target = SimpleNamespace(book_id="b1", title="Target")

    engine = _make_engine(
        books=[target],
        reviews_by_book={"b1": [SimpleNamespace(body="x")]},
        profile_scores_by_book={"b1": {"happy": 100}},
        review_scores={"happy": 100},
    )

    assert engine.recommend_content_based("u1", "b1", 2, "x") == []
    assert engine.recommend_content_based("u1", "b1", 4, "x") == []
    assert engine.recommend_content_based("u1", "b1", 5, "x") == []


def test_require_db_uses_review_service_db_and_raises_when_missing(db):
    engine_with_fallback = _make_engine(books=[], review_service_db=db)
    assert engine_with_fallback._require_db() is db

    engine_without_any_db = _make_engine(books=[])
    with pytest.raises(NotImplementedError, match="Database session not configured"):
        engine_without_any_db._require_db()


def test_get_review_texts_prefers_body_then_comment():
    b1 = SimpleNamespace(book_id="b1", title="Target")
    reviews = [
        SimpleNamespace(body="from body", comment="from comment"),
        SimpleNamespace(body=None, comment="only comment"),
        SimpleNamespace(body=None, comment=None),
    ]
    engine = _make_engine(books=[b1], reviews_by_book={"b1": reviews})

    assert engine._get_review_texts("b1") == ["from body", "only comment"]


def test_cosine_similarity_empty_and_zero_norm():
    engine = _make_engine(books=[])

    assert engine._cosine_similarity({}, {}) == 0.0
    assert engine._cosine_similarity({"happy": 0.0}, {"happy": 1.0}) == 0.0


def test_recommend_by_mood_non_zero_similarity_path():
    books = [
        SimpleNamespace(book_id="b1", title="Read"),
        SimpleNamespace(book_id="b2", title="Top Match"),
        SimpleNamespace(book_id="b3", title="Weaker Match"),
    ]

    engine = _make_engine(
        books=books,
        read_ids={"b1"},
        review_scores={"happy": 100.0},
        profile_scores_by_book={
            "b2": {"happy": 100.0},
            "b3": {"happy": 50.0, "sad": 50.0},
        },
        reviews_by_book={"b2": [SimpleNamespace(body="a")], "b3": [SimpleNamespace(body="b")]},
    )

    out = engine.recommend_by_mood("u1", "happy", top_n=2)
    assert [r["book"].book_id for r in out] == ["b2", "b3"]
    assert out[0]["similarity"] > out[1]["similarity"]


def test_recommend_by_mood_fallback_to_top_rated_when_no_similarity():
    books = [
        SimpleNamespace(book_id="b1", title="Read"),
        SimpleNamespace(book_id="b2", title="High Rated"),
        SimpleNamespace(book_id="b3", title="Low Rated"),
    ]

    engine = _make_engine(
        books=books,
        read_ids={"b1"},
        review_scores={},
        profile_scores_by_book={"b2": {"sad": 100}, "b3": {"sad": 100}},
        avg_by_book={"b2": 4.8, "b3": 2.1},
    )

    out = engine.recommend_by_mood("u1", "unmappedmood", top_n=2)
    assert [r["book"].book_id for r in out] == ["b2", "b3"]
    assert all(r["similarity"] == 0.0 for r in out)


def test_recommend_by_book_similarity_include_none_avg_when_required():
    books = [
        SimpleNamespace(book_id="b1", title="Target"),
        SimpleNamespace(book_id="b2", title="No Avg"),
        SimpleNamespace(book_id="b3", title="Lower Avg"),
    ]

    engine = _make_engine(
        books=books,
        avg_by_book={"b1": 4.0, "b2": None, "b3": 3.0},
        profile_scores_by_book={
            "b1": {"happy": 100},
            "b2": {"happy": 100},
            "b3": {"happy": 100},
        },
        reviews_by_book={"b1": [SimpleNamespace(body="x")]},
    )

    out = engine._recommend_by_book_similarity(
        target_book_id="b1",
        target_scores={"happy": 100},
        read_book_ids={"b1"},
        require_higher_rating=True,
    )

    assert [r["book"].book_id for r in out] == ["b2"]


def test_recommend_by_review_emotions_no_candidates_returns_empty():
    target = SimpleNamespace(book_id="b1", title="Target")
    engine = _make_engine(books=[target])

    out = engine._recommend_by_review_emotions(
        review_scores={"happy": 100},
        read_book_ids={"b1"},
        contrast_mode=False,
    )
    assert out == []


def test_recommend_by_book_similarity_no_candidates_returns_empty():
    target = SimpleNamespace(book_id="b1", title="Target")
    engine = _make_engine(
        books=[target],
        avg_by_book={"b1": 4.0},
        profile_scores_by_book={"b1": {"happy": 100}},
    )

    out = engine._recommend_by_book_similarity(
        target_book_id="b1",
        target_scores={"happy": 100},
        read_book_ids={"b1"},
        require_higher_rating=False,
    )
    assert out == []


def test_recommend_collaborative_candidate_filter_and_missing_book_branches(db):
    books = [SimpleNamespace(book_id="b1", title="Target")]
    review_texts = {
        "b1": [
            SimpleNamespace(body="good", user_id="u1"),
            SimpleNamespace(body="good", user_id="u2"),
        ]
    }
    engine = _make_engine(
        books=books,
        reviews_by_book=review_texts,
        review_scores={"happy": 100},
        profile_scores_by_book={"b1": {"happy": 100}},
        db=db,
    )

    # Candidate exists but is filtered out because user already read it -> line 272
    engine.bookshelf_service = _BookshelfService(read_ids={"cand-1"})
    monkey_reviews = [
        SimpleNamespace(user_id="u2", rating=5, book_id="cand-1"),
    ]
    db.execute = lambda stmt: SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: monkey_reviews))
    assert engine.recommend_collaborative("u1", "b1", "good") == []

    # Candidate survives filtering but missing book in catalog -> line 285
    engine.bookshelf_service = _BookshelfService(read_ids=set())
    monkey_reviews2 = [
        SimpleNamespace(user_id="u2", rating=5, book_id="not-in-catalog"),
    ]
    db.execute = lambda stmt: SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: monkey_reviews2))
    assert engine.recommend_collaborative("u1", "b1", "good") == []


def test_recommend_collaborative_handles_nan_book_id_branch_and_none_overall_avg(db):
    books = [
        SimpleNamespace(book_id="b1", title="Target"),
        SimpleNamespace(book_id="cand-2", title="Candidate"),
    ]
    review_texts = {
        "b1": [
            SimpleNamespace(body="good", user_id="u1"),
            SimpleNamespace(body="good", user_id="u2"),
            SimpleNamespace(body="good", user_id="u3"),
        ]
    }
    engine = _make_engine(
        books=books,
        reviews_by_book=review_texts,
        review_scores={"happy": 100},
        profile_scores_by_book={"b1": {"happy": 100}},
        avg_by_book={"cand-2": None},
        db=db,
    )

    nan_id = float("nan")
    monkey_reviews = [
        # Forces line 281: bid is NaN, so (r.book_id == bid) is False and ratings list is empty.
        SimpleNamespace(user_id="u2", rating=5, book_id=nan_id),
        SimpleNamespace(user_id="u2", rating=4, book_id="cand-2"),
        SimpleNamespace(user_id="u3", rating=5, book_id="cand-2"),
    ]
    db.execute = lambda stmt: SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: monkey_reviews))

    out = engine.recommend_collaborative("u1", "b1", "good")

    assert len(out) == 1
    assert out[0]["book"].book_id == "cand-2"
    # overall_avg is None so branch falls back to similar_user_avg.
    assert out[0]["score"] == pytest.approx(4.5)
