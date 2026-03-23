import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.mood_recommendation.recommendation_engine import RecommendationEngine


class FakeBook:
    def __init__(self, book_id, title, emotion_profile=None):
        self.book_id = book_id
        self.title = title
        self.emotion_profile = emotion_profile


class FakeReview:
    def __init__(self, body=None, comment=None, user_id=None, rating=None, book_id=None):
        self.body = body
        self.comment = comment
        self.user_id = user_id
        self.rating = rating
        self.book_id = book_id


class FakeBookService:
    def __init__(self, books):
        self._books = {b.book_id: b for b in books}

    def get_books(self):
        return list(self._books.values())

    def get_book(self, book_id):
        return self._books.get(book_id)


class FakeReviewService:
    def __init__(self, reviews_by_book, avg_by_book, db=None):
        self._reviews_by_book = reviews_by_book
        self._avg_by_book = avg_by_book
        self.db = db

    def get_reviews_by_book_id(self, book_id, **kwargs):
        return self._reviews_by_book.get(book_id, [])

    def get_average_rating(self, book_id):
        return self._avg_by_book.get(book_id)


class FakeBookshelfService:
    def __init__(self, read_book_ids):
        self._read_book_ids = set(read_book_ids)

    def list_shelf(self, user_id, status="read", **kwargs):
        class Item:
            def __init__(self, book_id):
                self.book_id = book_id

        return [Item(bid) for bid in self._read_book_ids]


class FakeEmotionExtractor:
    def __init__(self, default_scores=None, scores_by_text=None):
        self.default_scores = default_scores or {}
        self.scores_by_text = scores_by_text or {}

    def extract_emotions(self, review_text):
        scores = self.scores_by_text.get(review_text, self.default_scores)
        return {"scores": dict(scores)}


class FakeEmotionProfiler:
    def __init__(self, scores_by_book_id):
        self._scores_by_book_id = scores_by_book_id

    def create_book_profile(self, book_id, book_title, reviews):
        return {
            "title": book_title,
            "num_reviews": len(reviews),
            "emotion_scores": dict(self._scores_by_book_id.get(book_id, {})),
            "emotion_counts": {},
        }


class RecommendationEngineTests(unittest.TestCase):
    def _make_engine(
        self,
        *,
        books,
        reviews_by_book,
        avg_by_book,
        read_book_ids,
        review_scores=None,
        scores_by_text=None,
        book_scores=None,
        db=None,
        review_service_db=None,
    ):
        emotion_extractor = FakeEmotionExtractor(
            default_scores=review_scores or {},
            scores_by_text=scores_by_text,
        )
        engine = RecommendationEngine(
            book_service=FakeBookService(books),
            review_service=FakeReviewService(reviews_by_book, avg_by_book, db=review_service_db),
            bookshelf_service=FakeBookshelfService(read_book_ids),
            emotion_extractor_instance=emotion_extractor,
            emotion_profiler_instance=FakeEmotionProfiler(book_scores or {}),
            db=db,
        )
        return engine

    def test_init_uses_default_emotion_dependencies_when_not_injected(self):
        default_extractor = object()
        default_profiler = object()

        with patch(
            "app.services.mood_recommendation.emotion_extractor.emotion_extractor",
            default_extractor,
        ), patch(
            "app.services.mood_recommendation.emotion_profiler.get_book_profiler",
            return_value=default_profiler,
        ) as mock_factory:
            engine = RecommendationEngine(
                book_service=MagicMock(),
                review_service=MagicMock(),
                bookshelf_service=MagicMock(),
            )

        self.assertIs(engine.emotion_extractor, default_extractor)
        self.assertIs(engine.emotion_profiler, default_profiler)
        mock_factory.assert_called_once_with(default_extractor)

    def test_get_emotion_profile_uses_saved_profile_from_db(self):
        saved_profile = json.dumps(
            {
                "joy": {"score": 80.0, "count": 4},
                "fear": {"score": 20.0, "count": 1},
            }
        )
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = FakeBook(
            "b1",
            "Target",
            emotion_profile=saved_profile,
        )
        engine = self._make_engine(
            books=[FakeBook("b1", "Target")],
            reviews_by_book={},
            avg_by_book={},
            read_book_ids=set(),
            db=db,
        )

        profile = engine.get_emotion_profile("b1", "Target", ["r1", "r2"])

        self.assertEqual(profile["emotion_scores"], {"joy": 80.0, "fear": 20.0})
        self.assertEqual(profile["emotion_counts"], {"joy": 4, "fear": 1})
        self.assertEqual(profile["num_reviews"], 2)

    def test_get_emotion_profile_falls_back_on_invalid_saved_profile(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = FakeBook(
            "b1",
            "Target",
            emotion_profile="{invalid-json",
        )
        engine = self._make_engine(
            books=[FakeBook("b1", "Target")],
            reviews_by_book={},
            avg_by_book={},
            read_book_ids=set(),
            db=db,
            book_scores={"b1": {"joy": 100.0}},
        )

        profile = engine.get_emotion_profile("b1", "Target", ["r1"])

        self.assertEqual(profile["emotion_scores"], {"joy": 100.0})
        self.assertEqual(profile["num_reviews"], 1)

    def test_get_emotion_profile_falls_back_when_saved_profile_is_missing(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = FakeBook(
            "b1",
            "Target",
            emotion_profile=None,
        )
        engine = self._make_engine(
            books=[FakeBook("b1", "Target")],
            reviews_by_book={},
            avg_by_book={},
            read_book_ids=set(),
            db=db,
            book_scores={"b1": {"joy": 55.0}},
        )

        profile = engine.get_emotion_profile("b1", "Target", ["r1"])

        self.assertEqual(profile["emotion_scores"], {"joy": 55.0})

    def test_get_emotion_profile_falls_back_when_db_query_fails(self):
        db = MagicMock()
        db.query.side_effect = RuntimeError("db unavailable")
        engine = self._make_engine(
            books=[FakeBook("b1", "Target")],
            reviews_by_book={},
            avg_by_book={},
            read_book_ids=set(),
            db=db,
            book_scores={"b1": {"joy": 75.0}},
        )

        profile = engine.get_emotion_profile("b1", "Target", ["r1"])

        self.assertEqual(profile["emotion_scores"], {"joy": 75.0})

    def test_get_user_moods_requires_db(self):
        engine = self._make_engine(
            books=[],
            reviews_by_book={},
            avg_by_book={},
            read_book_ids=set(),
        )

        with self.assertRaises(NotImplementedError):
            engine.get_user_moods("u1")

    def test_get_user_moods_returns_rows(self):
        mood_rows = [SimpleNamespace(user_id="u1"), SimpleNamespace(user_id="u1")]
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = mood_rows
        engine = self._make_engine(
            books=[],
            reviews_by_book={},
            avg_by_book={},
            read_book_ids=set(),
            db=db,
        )

        self.assertEqual(engine.get_user_moods("u1"), mood_rows)

    def test_rating_low_contrast_mode(self):
        books = [FakeBook("b1", "Target"), FakeBook("b2", "LowSim"), FakeBook("b3", "HighSim")]
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b1": [FakeReview(body="x")]},
            avg_by_book={},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            book_scores={
                "b1": {"happy": 1.0},
                "b2": {"happy": 0.0},
                "b3": {"happy": 1.0},
            },
        )

        recs = engine.recommend_content_based("u1", "b1", 2, "sad")
        self.assertEqual(recs[0]["book"].book_id, "b2")
        self.assertIn("contrast_score", recs[0])

    def test_rating_low_similar_mode(self):
        books = [FakeBook("b1", "Target"), FakeBook("b2", "LowSim"), FakeBook("b3", "HighSim")]
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b1": [FakeReview(body="x")]},
            avg_by_book={},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            book_scores={
                "b1": {"sad": 1.0},
                "b2": {"happy": 0.2, "sad": 0.8},
                "b3": {"happy": 1.0},
            },
        )

        recs = engine.recommend_content_based("u1", "b1", 1, "sad")
        self.assertEqual(recs[0]["book"].book_id, "b3")
        self.assertNotIn("contrast_score", recs[0])

    def test_rating_mid_requires_higher_average(self):
        books = [
            FakeBook("b1", "Target"),
            FakeBook("b2", "LowerAvg"),
            FakeBook("b3", "HigherAvg"),
        ]
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b1": [FakeReview(body="x")]},
            avg_by_book={"b1": 3.5, "b2": 3.0, "b3": 4.2},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            book_scores={
                "b1": {"happy": 1.0},
                "b2": {"happy": 1.0},
                "b3": {"happy": 1.0},
            },
        )

        recs = engine.recommend_content_based("u1", "b1", 4, "nice")
        ids = [r["book"].book_id for r in recs]
        self.assertEqual(ids, ["b3"])

    def test_rating_mid_keeps_candidate_with_no_average(self):
        books = [FakeBook("b1", "Target"), FakeBook("b2", "UnknownAvg")]
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b1": [FakeReview(body="x")]},
            avg_by_book={"b1": 3.5, "b2": None},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            book_scores={"b1": {"happy": 1.0}, "b2": {"happy": 1.0}},
        )

        recs = engine.recommend_content_based("u1", "b1", 3, "ok")
        self.assertEqual([r["book"].book_id for r in recs], ["b2"])

    def test_rating_five_no_higher_requirement(self):
        books = [FakeBook("b1", "Target"), FakeBook("b2", "Candidate")]
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b1": [FakeReview(body="x")]},
            avg_by_book={"b1": 5.0, "b2": 2.0},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            book_scores={"b1": {"happy": 1.0}, "b2": {"happy": 1.0}},
        )

        recs = engine.recommend_content_based("u1", "b1", 5, "great")
        self.assertEqual(recs[0]["book"].book_id, "b2")

    def test_filters_out_read_books(self):
        books = [FakeBook("b1", "Target"), FakeBook("b2", "ReadBook"), FakeBook("b3", "Other")]
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b1": [FakeReview(body="x")]},
            avg_by_book={},
            read_book_ids={"b2"},
            review_scores={"happy": 1.0},
            book_scores={
                "b1": {"happy": 1.0},
                "b2": {"happy": 1.0},
                "b3": {"happy": 1.0},
            },
        )

        recs = engine.recommend_content_based("u1", "b1", 5, "great")
        ids = [r["book"].book_id for r in recs]
        self.assertNotIn("b2", ids)

    def test_target_book_missing_returns_empty(self):
        engine = self._make_engine(
            books=[FakeBook("b2", "Other")],
            reviews_by_book={},
            avg_by_book={},
            read_book_ids=set(),
        )

        self.assertEqual(engine.recommend_content_based("u1", "missing", 5, "great"), [])

    def test_invalid_rating_returns_empty(self):
        engine = self._make_engine(
            books=[FakeBook("b1", "Target")],
            reviews_by_book={"b1": [FakeReview(body="x")]},
            avg_by_book={},
            read_book_ids=set(),
            book_scores={"b1": {"happy": 1.0}},
        )

        self.assertEqual(engine.recommend_content_based("u1", "b1", 6, "great"), [])

    def test_rating_low_can_return_empty(self):
        engine = self._make_engine(
            books=[FakeBook("b1", "Target")],
            reviews_by_book={"b1": [FakeReview(body="x")]},
            avg_by_book={},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            book_scores={"b1": {"happy": 1.0}},
        )

        self.assertEqual(engine.recommend_content_based("u1", "b1", 2, "sad"), [])

    def test_rating_mid_can_return_empty(self):
        books = [FakeBook("b1", "Target"), FakeBook("b2", "LowerAvg")]
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b1": [FakeReview(body="x")]},
            avg_by_book={"b1": 4.0, "b2": 3.0},
            read_book_ids=set(),
            book_scores={"b1": {"happy": 1.0}, "b2": {"happy": 1.0}},
        )

        self.assertEqual(engine.recommend_content_based("u1", "b1", 3, "ok"), [])

    def test_rating_five_can_return_empty(self):
        engine = self._make_engine(
            books=[FakeBook("b1", "Target")],
            reviews_by_book={"b1": [FakeReview(body="x")]},
            avg_by_book={"b1": 5.0},
            read_book_ids=set(),
            book_scores={"b1": {"happy": 1.0}},
        )

        self.assertEqual(engine.recommend_content_based("u1", "b1", 5, "great"), [])

    def test_collaborative_filtering_no_similar_users(self):
        books = [FakeBook("b1", "Target")]
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b1": []},
            avg_by_book={"b1": 4.5},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            book_scores={"b1": {"happy": 1.0}},
            db=mock_db,
        )

        recs = engine.recommend_collaborative("u1", "b1", "good book")
        self.assertEqual(recs, [])

    def test_collaborative_filtering_personalized_weighting(self):
        books = [
            FakeBook("b1", "Target"),
            FakeBook("b2", "Candidate1"),
            FakeBook("b3", "Candidate2"),
        ]
        similar_user_reviews = [
            FakeReview(user_id="u2", rating=5, book_id="b2"),
            FakeReview(user_id="u3", rating=5, book_id="b2"),
            FakeReview(user_id="u2", rating=3, book_id="b3"),
            FakeReview(user_id="u3", rating=3, book_id="b3"),
        ]
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = similar_user_reviews
        engine = self._make_engine(
            books=books,
            reviews_by_book={
                "b1": [
                    FakeReview(body="good", user_id="u1"),
                    FakeReview(body="good", user_id="u2"),
                    FakeReview(body="good", user_id="u3"),
                ]
            },
            avg_by_book={"b2": 2.0, "b3": 5.0},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            book_scores={"b1": {"happy": 1.0}},
            db=mock_db,
        )

        recs = engine.recommend_collaborative("u1", "b1", "good book")
        self.assertGreater(len(recs), 0)
        self.assertEqual(recs[0]["book"].book_id, "b2")
        self.assertAlmostEqual(recs[0]["score"], 4.1, places=1)
        if len(recs) > 1:
            self.assertEqual(recs[1]["book"].book_id, "b3")
            self.assertAlmostEqual(recs[1]["score"], 3.6, places=1)

    def test_collaborative_filtering_falls_back_to_review_service_db(self):
        books = [FakeBook("b1", "Target"), FakeBook("b2", "Candidate")]
        similar_user_reviews = [FakeReview(user_id="u2", rating=5, book_id="b2")]
        fallback_db = MagicMock()
        fallback_db.execute.return_value.scalars.return_value.all.return_value = similar_user_reviews
        engine = self._make_engine(
            books=books,
            reviews_by_book={
                "b1": [
                    FakeReview(body="great", user_id="u1"),
                    FakeReview(body="great", user_id="u2"),
                ]
            },
            avg_by_book={"b2": None},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            scores_by_text={"great": {"happy": 1.0}},
            book_scores={"b1": {"happy": 1.0}},
            review_service_db=fallback_db,
        )

        recs = engine.recommend_collaborative("u1", "b1", "great")
        self.assertEqual(recs[0]["book"].book_id, "b2")
        self.assertEqual(recs[0]["score"], 5.0)

    def test_collaborative_filtering_returns_empty_when_candidates_are_already_read(self):
        books = [FakeBook("b1", "Target"), FakeBook("b2", "Candidate")]
        similar_user_reviews = [FakeReview(user_id="u2", rating=5, book_id="b2")]
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = similar_user_reviews
        engine = self._make_engine(
            books=books,
            reviews_by_book={
                "b1": [
                    FakeReview(body="great", user_id="u1"),
                    FakeReview(body="great", user_id="u2"),
                ]
            },
            avg_by_book={"b2": 4.5},
            read_book_ids={"b2"},
            review_scores={"happy": 1.0},
            scores_by_text={"great": {"happy": 1.0}},
            db=db,
        )

        self.assertEqual(engine.recommend_collaborative("u1", "b1", "great"), [])

    def test_collaborative_filtering_keeps_highest_similarity_per_user(self):
        books = [FakeBook("b1", "Target"), FakeBook("b2", "Candidate")]
        similar_user_reviews = [FakeReview(user_id="u2", rating=5, book_id="b2")]
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = similar_user_reviews
        engine = self._make_engine(
            books=books,
            reviews_by_book={
                "b1": [
                    FakeReview(body="seed", user_id="u1"),
                    FakeReview(body="match", user_id="u2"),
                    FakeReview(body="mismatch", user_id="u2"),
                ]
            },
            avg_by_book={"b2": 4.0},
            read_book_ids=set(),
            scores_by_text={
                "seed": {"happy": 1.0},
                "match": {"happy": 1.0},
                "mismatch": {"sad": 1.0},
            },
            db=db,
        )

        recs = engine.recommend_collaborative("u1", "b1", "seed")
        self.assertEqual(recs[0]["book"].book_id, "b2")

    def test_collaborative_filtering_skips_missing_book(self):
        books = [FakeBook("b1", "Target")]
        similar_user_reviews = [FakeReview(user_id="u2", rating=5, book_id="missing-book")]
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = similar_user_reviews
        engine = self._make_engine(
            books=books,
            reviews_by_book={
                "b1": [
                    FakeReview(body="great", user_id="u1"),
                    FakeReview(body="great", user_id="u2"),
                ]
            },
            avg_by_book={"missing-book": 4.5},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            scores_by_text={"great": {"happy": 1.0}},
            db=db,
        )

        self.assertEqual(engine.recommend_collaborative("u1", "b1", "great"), [])

    def test_collaborative_filtering_skips_candidate_without_ratings(self):
        class FlakyReview(FakeReview):
            def __init__(self, user_id, rating, first_book_id, later_book_id):
                super().__init__(body="match", user_id=user_id, rating=rating, book_id=None)
                self._first_book_id = first_book_id
                self._later_book_id = later_book_id
                self._access_count = 0

            @property
            def book_id(self):
                self._access_count += 1
                if self._access_count == 1:
                    return self._first_book_id
                return self._later_book_id

            @book_id.setter
            def book_id(self, value):
                return None

        books = [FakeBook("b1", "Target"), FakeBook("b2", "Candidate")]
        similar_user_reviews = [FlakyReview("u2", 5, "b2", "different-book")]
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = similar_user_reviews
        engine = self._make_engine(
            books=books,
            reviews_by_book={
                "b1": [
                    FakeReview(body="seed", user_id="u1"),
                    FakeReview(body="match", user_id="u2"),
                ]
            },
            avg_by_book={"b2": 4.0},
            read_book_ids=set(),
            scores_by_text={"seed": {"happy": 1.0}, "match": {"happy": 1.0}},
            db=db,
        )

        self.assertEqual(engine.recommend_collaborative("u1", "b1", "seed"), [])

    def test_require_db_raises_when_missing_everywhere(self):
        engine = self._make_engine(
            books=[],
            reviews_by_book={},
            avg_by_book={},
            read_book_ids=set(),
        )

        with self.assertRaises(NotImplementedError):
            engine._require_db()

    def test_get_review_texts_prefers_body_then_comment(self):
        engine = self._make_engine(
            books=[],
            reviews_by_book={
                "b1": [
                    FakeReview(body="body text", comment="comment text"),
                    FakeReview(body=None, comment="comment only"),
                    FakeReview(body=None, comment=None),
                ]
            },
            avg_by_book={},
            read_book_ids=set(),
        )

        self.assertEqual(engine._get_review_texts("b1"), ["body text", "comment only"])

    def test_recommend_by_review_emotions_returns_empty_when_everything_is_read(self):
        books = [FakeBook("b1", "Target")]
        engine = self._make_engine(
            books=books,
            reviews_by_book={},
            avg_by_book={},
            read_book_ids={"b1"},
            review_scores={"happy": 1.0},
        )

        self.assertEqual(
            engine._recommend_by_review_emotions({"happy": 1.0}, {"b1"}, contrast_mode=False),
            [],
        )

    def test_recommend_by_book_similarity_returns_empty_when_everything_is_filtered(self):
        books = [FakeBook("b1", "Target"), FakeBook("b2", "Filtered")]
        engine = self._make_engine(
            books=books,
            reviews_by_book={},
            avg_by_book={"b1": 4.0, "b2": 3.0},
            read_book_ids={"b2"},
            book_scores={"b2": {"happy": 1.0}},
        )

        self.assertEqual(
            engine._recommend_by_book_similarity(
                target_book_id="b1",
                target_scores={"happy": 1.0},
                read_book_ids={"b1", "b2"},
                require_higher_rating=True,
            ),
            [],
        )

    def test_cosine_similarity_handles_empty_inputs_and_zero_norm(self):
        engine = self._make_engine(
            books=[],
            reviews_by_book={},
            avg_by_book={},
            read_book_ids=set(),
        )

        self.assertEqual(engine._cosine_similarity({}, {}), 0.0)
        self.assertEqual(engine._cosine_similarity({"happy": 0.0}, {"happy": 1.0}), 0.0)

    def test_recommend_by_mood_returns_non_zero_matches(self):
        books = [FakeBook("b1", "Read"), FakeBook("b2", "Happy Book"), FakeBook("b3", "Sad Book")]
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b2": [FakeReview(body="joy")], "b3": [FakeReview(body="sorrow")]},
            avg_by_book={"b2": 4.0, "b3": 5.0},
            read_book_ids={"b1"},
            scores_by_text={"happy": {"happy": 100.0}},
            book_scores={"b2": {"happy": 100.0}, "b3": {"sad": 100.0}},
        )

        recs = engine.recommend_by_mood("u1", "happy", top_n=2)
        self.assertEqual([r["book"].book_id for r in recs], ["b2"])
        self.assertGreater(recs[0]["similarity"], 0.0)

    def test_recommend_by_mood_falls_back_to_literal_mood_and_top_rated_books(self):
        books = [FakeBook("b1", "Read"), FakeBook("b2", "Top Rated"), FakeBook("b3", "Other")]
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b2": [FakeReview(body="x")], "b3": [FakeReview(body="y")]},
            avg_by_book={"b2": 4.8, "b3": 3.7},
            read_book_ids={"b1"},
            scores_by_text={"mysterious": {}},
            book_scores={"b2": {"joy": 100.0}, "b3": {"sad": 100.0}},
        )

        recs = engine.recommend_by_mood("u1", "mysterious", top_n=2)
        self.assertEqual([r["book"].book_id for r in recs], ["b2", "b3"])
        self.assertEqual([r["similarity"] for r in recs], [0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
