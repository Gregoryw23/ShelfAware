from __future__ import annotations

from typing import Optional, Any, TYPE_CHECKING
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mood import Mood
from app.models.review import Review

if TYPE_CHECKING:
    from app.services.book_service import BookService
    from app.services.review_service import ReviewService
    from app.services.bookshelf_service import BookshelfService
    from app.services.mood_recommendation.emotion_extractor import EmotionExtractor
    from app.services.mood_recommendation.emotion_profiler import BookEmotionProfiler


class RecommendationEngine:
    """
    Lightweight wiring class for the mood-based recommendation feature.

    This class implements content-based recommendations driven by emotion profiles.
    """

    def __init__(
        self,
        *,
        book_service: BookService,
        review_service: ReviewService,
        bookshelf_service: BookshelfService,
        db: Optional[Session] = None,
        emotion_extractor_instance: Optional[EmotionExtractor] = None,
        emotion_profiler_instance: Optional[BookEmotionProfiler] = None,
    ) -> None:
        # Core services for pulling data
        self.book_service = book_service
        self.review_service = review_service
        self.bookshelf_service = bookshelf_service
        # Optional DB session used for mood lookup
        self.db = db

        # Emotion tools (allow injection for testing)
        if emotion_extractor_instance is None:
            from app.services.mood_recommendation.emotion_extractor import emotion_extractor
            self.emotion_extractor = emotion_extractor
        else:
            self.emotion_extractor = emotion_extractor_instance

        if emotion_profiler_instance is None:
            from app.services.mood_recommendation.emotion_profiler import get_book_profiler
            self.emotion_profiler = get_book_profiler(self.emotion_extractor)
        else:
            self.emotion_profiler = emotion_profiler_instance

    # --- Data access wrappers ---
    def get_books(self):
        """Fetch all books via BookService."""
        return self.book_service.get_books()

    def get_reviews_for_book(self, book_id, **kwargs):
        """Fetch reviews for a book via ReviewService."""
        return self.review_service.get_reviews_by_book_id(book_id, **kwargs)

    def get_emotion_profile(self, book_id, book_title, reviews):
        """
        Get or build an emotion profile for a book.
        
        First tries to load from saved book.emotion_profile DB column (JSON).
        Falls back to building from reviews if not saved.
        """
        # Try to load saved profile from DB if we have a session
        if self.db is not None:
            try:
                from app.models.book import Book
                book = self.db.query(Book).filter(Book.book_id == book_id).first()
                if book and book.emotion_profile:
                    try:
                        saved_profile = json.loads(book.emotion_profile)
                        # Convert saved format back to expected format
                        emotion_scores = {
                            emotion: data.get("score", 0.0) 
                            for emotion, data in saved_profile.items()
                        }
                        emotion_counts = {
                            emotion: data.get("count", 0) 
                            for emotion, data in saved_profile.items()
                        }
                        print(f"  ✓ Loaded saved profile for book {book_id} from DB")
                        return {
                            'title': book_title,
                            'num_reviews': len(reviews),
                            'emotion_scores': emotion_scores,
                            'emotion_counts': emotion_counts
                        }
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"  ⚠ Failed to parse saved profile: {e}, building fresh")
            except Exception as e:
                print(f"  ⚠ Could not load saved profile: {e}, building fresh")
        
        # Fall back to building from reviews
        return self.emotion_profiler.create_book_profile(book_id, book_title, reviews)

    def get_user_read_books(self, user_id: Any, **kwargs):
        """Return books the user has finished reading via BookshelfService."""
        return self.bookshelf_service.list_shelf(user_id=user_id, status="read", **kwargs)

    # Mood entries are stored via ReviewService into Mood rows
    def get_user_moods(self, user_id: Any):
        """Return all mood entries for the user (requires DB session)."""
        if self.db is None:
            raise NotImplementedError("Database session not configured for mood lookup")
        stmt = select(Mood).where(Mood.user_id == user_id)
        return self.db.execute(stmt).scalars().all()

    # --- Content-based recommendation logic ---
    def recommend_content_based(self, user_id, book_id, rating, review_text):
        """
        Recommend books based on the provided rating + review_text and emotion profiles.

        Returns a list of up to 5 dicts: {"book": <Book>, "similarity": <float>}.
        In contrast mode, also includes: {"contrast_score": <float>}.
        """
        print(f"\n{'='*60}")
        print(f"RECOMMENDATION DEBUG START")
        print(f"{'='*60}")
        print(f"Input: user_id={user_id}, book_id={book_id}, rating={rating}")
        print(f"Review text: '{review_text}'")

        # Build read set to filter out previously read books
        read_items = self.get_user_read_books(user_id)
        read_book_ids = {item.book_id for item in read_items}
        read_book_ids.add(book_id)
        print(f"\n[STEP 4] User's Bookshelf:")
        print(f"  User has read {len(read_book_ids)} books")
        print(f"  Read book IDs: {read_book_ids}")

        # Prepare target book profile
        target_book = self.book_service.get_book(book_id)
        if not target_book:
            print("  WARNING: target book not found; returning []")
            print(f"{'='*60}\n")
            return []

        target_reviews = self._get_review_texts(book_id)
        target_profile = self.get_emotion_profile(book_id, target_book.title, target_reviews)
        target_scores = target_profile.get("emotion_scores", {})
        print(f"\n[STEP 2] Book Emotion Profile:")
        print(f"  Book {book_id} emotions: {target_scores}")
        print(f"  Is empty?: {len(target_scores) == 0}")

        # For debugging, list DB books
        all_books = list(self.get_books())
        print(f"\n[STEP 5] Database Books:")
        print(f"  Total books in database: {len(all_books)}")
        print(f"  Book IDs: {[getattr(book, 'book_id', getattr(book, 'id', None)) for book in all_books[:10]]}...")

        if rating < 3:
            review_scores = self._extract_review_scores(review_text)
            print(f"\n[STEP 1] Review Emotion Extraction:")
            print(f"  Review emotions: {review_scores}")
            print(f"  Is empty?: {len(review_scores) == 0}")

            base_similarity = self._cosine_similarity(review_scores, target_scores)
            print(f"\n[STEP 3] Similarity Calculation:")
            print(f"  Base similarity: {base_similarity}")

            contrast_mode = base_similarity > 0.50
            result = self._recommend_by_review_emotions(
                review_scores,
                read_book_ids,
                contrast_mode=contrast_mode,
            )
            print(f"\n[STEP 8] Final Result:")
            print(f"  Returning {len(result)} recommendations")
            if len(result) > 0:
                print(f"  Top recommendation: {result[0]}")
            else:
                print(f"  WARNING: Returning empty list!")
            print(f"{'='*60}\n")
            return result

        if rating in (3, 4):
            # include current average rating in the downstream logs via review_service
            print(f"\n[INFO] Rating in (3,4); using book similarity with require_higher_rating=True")
            result = self._recommend_by_book_similarity(
                target_book_id=book_id,
                target_scores=target_scores,
                read_book_ids=read_book_ids,
                require_higher_rating=True,
            )
            print(f"\n[STEP 8] Final Result:")
            print(f"  Returning {len(result)} recommendations")
            if len(result) > 0:
                print(f"  Top recommendation: {result[0]}")
            else:
                print(f"  WARNING: Returning empty list!")
            print(f"{'='*60}\n")
            return result

        if rating == 5:
            print(f"\n[INFO] Rating == 5; using book similarity with require_higher_rating=False")
            result = self._recommend_by_book_similarity(
                target_book_id=book_id,
                target_scores=target_scores,
                read_book_ids=read_book_ids,
                require_higher_rating=False,
            )
            print(f"\n[STEP 8] Final Result:")
            print(f"  Returning {len(result)} recommendations")
            if len(result) > 0:
                print(f"  Top recommendation: {result[0]}")
            else:
                print(f"  WARNING: Returning empty list!")
            print(f"{'='*60}\n")
            return result

        print(f"{'='*60}\n")
        return []

    # --- Collaborative filtering logic ---
    def recommend_collaborative(self, user_id, book_id, review_text):
        """
        Recommend books using collaborative filtering with emotion similarity.

        Uses personalized weighting: similar user ratings (70%) are prioritized over
        general ratings (30%) to ensure personalized touch.

        Returns a list of up to 5 dicts: {"book": <Book>, "score": <float>}.
        Score is the weighted average: 70% similar users + 30% overall average.
        """
        db = self._require_db()

        # Current user's review emotions for this book
        user_scores = self._extract_review_scores(review_text)

        # Get all reviews for the same book and compare emotions
        reviews = self.get_reviews_for_book(book_id, limit=500)
        similarity_by_user: dict[str, float] = {}
        for r in reviews:
            if getattr(r, "user_id", None) == user_id:
                continue
            other_text = getattr(r, "body", None) or getattr(r, "comment", None) or ""
            other_scores = self._extract_review_scores(other_text)
            sim = self._cosine_similarity(user_scores, other_scores)
            if sim > similarity_by_user.get(r.user_id, -1.0):
                similarity_by_user[r.user_id] = sim

        if not similarity_by_user:
            return []

        # Top 5 most similar users
        top_users = [u for u, _ in sorted(similarity_by_user.items(), key=lambda x: x[1], reverse=True)[:5]]

        # Books those users rated 4-5
        stmt = (
            select(Review)
            .where(Review.user_id.in_(top_users))
            .where(Review.rating >= 4)
        )
        similar_user_reviews = db.execute(stmt).scalars().all()
        candidate_book_ids = {r.book_id for r in similar_user_reviews}

        # Filter out user's read books
        read_items = self.get_user_read_books(user_id)
        read_book_ids = {item.book_id for item in read_items}
        read_book_ids.add(book_id)

        candidate_book_ids = {bid for bid in candidate_book_ids if bid not in read_book_ids}
        if not candidate_book_ids:
            return []

        # Rank by personalized weighting: similar user ratings (70%) > overall rating (30%)
        scored = []
        for bid in candidate_book_ids:
            # Get all ratings from similar users for this book
            similar_user_ratings = [r.rating for r in similar_user_reviews if r.book_id == bid]
            
            if not similar_user_ratings:
                continue
            
            book = self.book_service.get_book(bid)
            if not book:
                continue
            
            # Calculate weighted score: prioritize similar user preferences
            similar_user_avg = sum(similar_user_ratings) / len(similar_user_ratings)
            overall_avg = self.review_service.get_average_rating(bid)
            
            # Fallback to similar user average if overall not available
            if overall_avg is None:
                overall_avg = similar_user_avg
            
            # Weighted combination: 70% similar users, 30% overall
            weighted_score = (0.7 * similar_user_avg) + (0.3 * overall_avg)
            
            scored.append({"book": book, "score": weighted_score})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:5]

    def _require_db(self) -> Session:
        if self.db is not None:
            return self.db
        if getattr(self.review_service, "db", None) is not None:
            return self.review_service.db
        raise NotImplementedError("Database session not configured for collaborative filtering")

    def _extract_review_scores(self, review_text: str) -> dict:
        result = self.emotion_extractor.extract_emotions(review_text or "")
        return result.get("scores", {})

    def _get_review_texts(self, book_id) -> list[str]:
        reviews = self.get_reviews_for_book(book_id, limit=500)
        texts: list[str] = []
        for r in reviews:
            body = getattr(r, "body", None)
            comment = getattr(r, "comment", None)
            if body:
                texts.append(body)
            elif comment:
                texts.append(comment)
        return texts

    def _recommend_by_review_emotions(self, review_scores: dict, read_book_ids: set, *, contrast_mode: bool):
        candidates = []
        for book in self.get_books():
            if book.book_id in read_book_ids:
                continue
            print(f"\n[STEP 6] Checking candidate book {book.book_id}: {getattr(book, 'title', None)}")
            print(f"  - Is target book?: {book.book_id == getattr(book, 'book_id', book.book_id)}")
            print(f"  - Is in bookshelf?: {book.book_id in read_book_ids}")
            profile = self.get_emotion_profile(book.book_id, book.title, self._get_review_texts(book.book_id))
            book_scores = profile.get("emotion_scores", {})
            print(f"  - Candidate emotions: {book_scores}")
            similarity = self._cosine_similarity(review_scores, book_scores)
            print(f"  - Similarity score: {similarity}")
            score = 1.0 - similarity if contrast_mode else similarity
            candidates.append({"book": book, "similarity": similarity, "_score": score})

        print(f"\n[STEP 7] Before Sorting:")
        print(f"  Total recommendations: {len(candidates)}")
        if len(candidates) > 0:
            print(f"  Sample recommendation: {candidates[0]}")

        candidates.sort(key=lambda x: x["_score"], reverse=True)
        results = []
        for c in candidates[:5]:
            item = {"book": c["book"], "similarity": c["similarity"]}
            if contrast_mode:
                item["contrast_score"] = c["_score"]
            results.append(item)

        print(f"\n[STEP 8] Final Result:")
        print(f"  Returning {len(results)} recommendations")
        if len(results) > 0:
            print(f"  Top recommendation: {results[0]}")
        else:
            print(f"  WARNING: Returning empty list!")

        return results

    def _recommend_by_book_similarity(
        self,
        *,
        target_book_id,
        target_scores: dict,
        read_book_ids: set,
        require_higher_rating: bool,
    ):
        target_avg = self.review_service.get_average_rating(target_book_id)
        candidates = []

        for book in self.get_books():
            if book.book_id in read_book_ids:
                continue

            print(f"\n[STEP 6] Checking candidate book {book.book_id}: {getattr(book, 'title', None)}")
            print(f"  - Is target book?: {book.book_id == target_book_id}")
            print(f"  - Is in bookshelf?: {book.book_id in read_book_ids}")
            profile = self.get_emotion_profile(book.book_id, book.title, self._get_review_texts(book.book_id))
            book_scores = profile.get("emotion_scores", {})
            print(f"  - Candidate emotions: {book_scores}")
            similarity = self._cosine_similarity(target_scores, book_scores)
            print(f"  - Similarity score: {similarity}")

            if require_higher_rating and target_avg is not None:
                candidate_avg = self.review_service.get_average_rating(book.book_id)
                print(f"  - Current book rating: {target_avg}")
                print(f"  - Candidate rating: {candidate_avg}")
                # Include books with no rating; only skip if rated AND lower
                if candidate_avg is not None and candidate_avg <= target_avg:
                    print(f"  - Skipping: book has rating {candidate_avg} <= {target_avg}")
                    continue

            candidates.append({"book": book, "similarity": similarity})

        print(f"\n[STEP 7] Before Sorting:")
        print(f"  Total recommendations: {len(candidates)}")
        if len(candidates) > 0:
            print(f"  Sample recommendation: {candidates[0]}")

        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        results = candidates[:5]

        print(f"\n[STEP 8] Final Result:")
        print(f"  Returning {len(results)} recommendations")
        if len(results) > 0:
            print(f"  Top recommendation: {results[0]}")
        else:
            print(f"  WARNING: Returning empty list!")

        return results

    def _cosine_similarity(self, scores_a: dict, scores_b: dict) -> float:
        keys = sorted(set(scores_a.keys()) | set(scores_b.keys()))
        if not keys:
            return 0.0
        vec_a = [float(scores_a.get(k, 0.0)) for k in keys]
        vec_b = [float(scores_b.get(k, 0.0)) for k in keys]
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)
