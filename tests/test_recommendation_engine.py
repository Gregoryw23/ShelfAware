import unittest
from unittest.mock import MagicMock

from app.services.mood_recommendation.recommendation_engine import RecommendationEngine


class FakeBook:
    def __init__(self, book_id, title):
        self.book_id = book_id
        self.title = title


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
    def __init__(self, reviews_by_book, avg_by_book):
        self._reviews_by_book = reviews_by_book
        self._avg_by_book = avg_by_book
        self.db = None  # For collaborative filtering

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
    def __init__(self, review_scores):
        self._review_scores = review_scores

    def extract_emotions(self, review_text):
        return {"scores": dict(self._review_scores)}


class FakeEmotionProfiler:
    def __init__(self, scores_by_book_id):
        self._scores_by_book_id = scores_by_book_id

    def create_book_profile(self, book_id, book_title, reviews):
        return {"emotion_scores": dict(self._scores_by_book_id.get(book_id, {}))}


class FakeDatabase:
    """Mock database for testing collaborative filtering."""
    def __init__(self, all_reviews):
        self._all_reviews = all_reviews

    def execute(self, stmt):
        # Simplified mock: returns wrapper that supports scalars()
        return self

    def scalars(self):
        # Return all reviews (simplified for testing)
        return self

    def all(self):
        return self._all_reviews


class RecommendationEngineTests(unittest.TestCase):
    def _make_engine(self, *, books, reviews_by_book, avg_by_book, read_book_ids, review_scores, book_scores, db=None):
        engine = RecommendationEngine(
            book_service=FakeBookService(books),
            review_service=FakeReviewService(reviews_by_book, avg_by_book),
            bookshelf_service=FakeBookshelfService(read_book_ids),
            emotion_extractor_instance=FakeEmotionExtractor(review_scores),
            emotion_profiler_instance=FakeEmotionProfiler(book_scores),
            db=db,
        )
        return engine

    def test_rating_low_contrast_mode(self):
        # base similarity > 0.5 triggers contrast mode
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
        # base similarity <= 0.5 triggers similar mode
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

    def test_rating_five_no_higher_requirement(self):
        books = [
            FakeBook("b1", "Target"),
            FakeBook("b2", "Candidate"),
        ]
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b1": [FakeReview(body="x")]},
            avg_by_book={"b1": 5.0, "b2": 2.0},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            book_scores={
                "b1": {"happy": 1.0},
                "b2": {"happy": 1.0},
            },
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

    def test_collaborative_filtering_no_similar_users(self):
        """Test collaborative filtering returns empty when no similar users exist."""
        books = [FakeBook("b1", "Target")]
        
        # Create a mock DB that returns no reviews
        mock_db = MagicMock()
        mock_db.execute(MagicMock()).scalars().all.return_value = []
        
        engine = self._make_engine(
            books=books,
            reviews_by_book={"b1": []},  # No reviews from similar users
            avg_by_book={"b1": 4.5},
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            book_scores={"b1": {"happy": 1.0}},
            db=mock_db,
        )

        recs = engine.recommend_collaborative("u1", "b1", "good book")
        self.assertEqual(recs, [])

    def test_collaborative_filtering_personalized_weighting(self):
        """Test that similar user ratings are weighted higher (70%) than overall ratings (30%)."""
        books = [
            FakeBook("b1", "Target"),
            FakeBook("b2", "Candidate1"),
            FakeBook("b3", "Candidate2"),
        ]
        
        # Create reviews from similar users and overall ratings
        # b2: similar users rate 5, overall is 2 (low) -> weighted = 0.7*5 + 0.3*2 = 4.10
        # b3: similar users rate 3, overall is 5 (high) -> weighted = 0.7*3 + 0.3*5 = 3.60
        # Should recommend b2 first because similar users prefer it more
        similar_user_reviews = [
            FakeReview(user_id="u2", rating=5, book_id="b2"),
            FakeReview(user_id="u3", rating=5, book_id="b2"),
            FakeReview(user_id="u2", rating=3, book_id="b3"),
            FakeReview(user_id="u3", rating=3, book_id="b3"),
        ]
        
        mock_db = MagicMock()
        mock_db.execute(MagicMock()).scalars().all.return_value = similar_user_reviews
        
        engine = self._make_engine(
            books=books,
            # Include other users' reviews for the same book so similarity is computed
            reviews_by_book={"b1": [
                FakeReview(body="good", user_id="u1"),
                FakeReview(body="good", user_id="u2"),
                FakeReview(body="good", user_id="u3"),
            ]},
            avg_by_book={"b2": 2.0, "b3": 5.0},  # Opposite of similar user ratings
            read_book_ids=set(),
            review_scores={"happy": 1.0},
            book_scores={"b1": {"happy": 1.0}},
            db=mock_db,
        )

        recs = engine.recommend_collaborative("u1", "b1", "good book")
        
        # Should recommend b2 first (similar users rate it 5, weighted = 4.1)
        # Then b3 (similar users rate it 3, weighted = 3.6)
        self.assertGreater(len(recs), 0)
        self.assertEqual(recs[0]["book"].book_id, "b2")
        self.assertAlmostEqual(recs[0]["score"], 4.1, places=1)
        if len(recs) > 1:
            self.assertEqual(recs[1]["book"].book_id, "b3")
            self.assertAlmostEqual(recs[1]["score"], 3.6, places=1)


if __name__ == "__main__":
    unittest.main()
