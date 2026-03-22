import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.routes.recommendation_routes import (
    debug_get_book_emotions,
    debug_get_book_reviews,
    debug_get_user_bookshelf,
    recommend_content_based,
    recommend_collaborative,
)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock(spec=Session)


class TestDebugGetBookEmotions:
    """Test debug endpoint for book emotion profile."""

    def test_get_book_emotions_success(self, mock_db):
        """Test successful emotion retrieval."""
        with patch("app.routes.recommendation_routes.BookService") as MockBookService:
            with patch("app.routes.recommendation_routes.ReviewService") as MockReviewService:
                with patch("app.routes.recommendation_routes.get_recommendation_engine") as MockEngine:
                    mock_book_service = Mock()
                    mock_book = Mock(book_id="book-123", title="Test Book")
                    mock_book_service.get_book.return_value = mock_book
                    MockBookService.return_value = mock_book_service

                    mock_review_service = Mock()
                    mock_review = Mock(body="Great book!", comment="Amazing")
                    mock_review_service.get_reviews_by_book_id.return_value = [mock_review]
                    MockReviewService.return_value = mock_review_service

                    mock_engine = Mock()
                    mock_engine.get_emotion_profile.return_value = {
                        "joy": 0.8,
                        "anger": 0.2
                    }
                    MockEngine.return_value = mock_engine

                    result = debug_get_book_emotions(book_id="book-123", db=mock_db)

                    assert result["book_id"] == "book-123"
                    assert result["book_title"] == "Test Book"
                    assert "emotion_profile" in result

    def test_get_book_emotions_book_not_found(self, mock_db):
        """Test emotion retrieval when book not found."""
        with patch("app.routes.recommendation_routes.BookService") as MockBookService:
            mock_book_service = Mock()
            mock_book_service.get_book.return_value = None
            MockBookService.return_value = mock_book_service

            with pytest.raises(HTTPException) as exc_info:
                debug_get_book_emotions(book_id="nonexistent", db=mock_db)
            
            assert exc_info.value.status_code == 404
            assert "Book not found" in exc_info.value.detail

    def test_get_book_emotions_service_error(self, mock_db):
        """Test emotion retrieval with service error (line 206-207)."""
        with patch("app.routes.recommendation_routes.BookService") as MockBookService:
            mock_book_service = Mock()
            mock_book = Mock(book_id="book-123", title="Test Book")
            mock_book_service.get_book.return_value = mock_book
            MockBookService.return_value = mock_book_service

            with patch("app.routes.recommendation_routes.ReviewService") as MockReviewService:
                mock_review_service = Mock()
                mock_review_service.get_reviews_by_book_id.side_effect = Exception("DB error")
                MockReviewService.return_value = mock_review_service

                with pytest.raises(HTTPException) as exc_info:
                    debug_get_book_emotions(book_id="book-123", db=mock_db)
                
                assert exc_info.value.status_code == 400
                assert "Error fetching emotion profile" in exc_info.value.detail


class TestDebugGetBookReviews:
    """Test debug endpoint for book reviews."""

    def test_get_book_reviews_success(self, mock_db):
        """Test successful reviews retrieval."""
        with patch("app.routes.recommendation_routes.BookService") as MockBookService:
            with patch("app.routes.recommendation_routes.ReviewService") as MockReviewService:
                mock_book_service = Mock()
                mock_book = Mock(book_id="book-123", title="Test Book")
                mock_book_service.get_book.return_value = mock_book
                MockBookService.return_value = mock_book_service

                mock_review_service = Mock()
                mock_review = Mock(
                    review_id="rev-1",
                    user_id="user-1",
                    rating=5,
                    body="Great!"
                )
                mock_review_service.get_reviews_by_book_id.return_value = [mock_review]
                mock_review_service.get_average_rating.return_value = 4.5
                MockReviewService.return_value = mock_review_service

                result = debug_get_book_reviews(book_id="book-123", db=mock_db)

                assert result["book_id"] == "book-123"
                assert result["average_rating"] == 4.5
                assert len(result["reviews"]) == 1

    def test_get_book_reviews_book_not_found(self, mock_db):
        """Test reviews retrieval when book not found."""
        with patch("app.routes.recommendation_routes.BookService") as MockBookService:
            mock_book_service = Mock()
            mock_book_service.get_book.return_value = None
            MockBookService.return_value = mock_book_service

            with pytest.raises(HTTPException) as exc_info:
                debug_get_book_reviews(book_id="nonexistent", db=mock_db)
            
            assert exc_info.value.status_code == 404
            assert "Book not found" in exc_info.value.detail

    def test_get_book_reviews_service_error(self, mock_db):
        """Test reviews retrieval with service error (line 244-245)."""
        with patch("app.routes.recommendation_routes.BookService") as MockBookService:
            mock_book_service = Mock()
            mock_book = Mock(book_id="book-123", title="Test Book")
            mock_book_service.get_book.return_value = mock_book
            MockBookService.return_value = mock_book_service

            with patch("app.routes.recommendation_routes.ReviewService") as MockReviewService:
                mock_review_service = Mock()
                mock_review_service.get_reviews_by_book_id.side_effect = Exception("DB error")
                MockReviewService.return_value = mock_review_service

                with pytest.raises(HTTPException) as exc_info:
                    debug_get_book_reviews(book_id="book-123", db=mock_db)
                
                assert exc_info.value.status_code == 400
                assert "Error fetching reviews" in exc_info.value.detail


class TestDebugGetUserBookshelf:
    """Test debug endpoint for user bookshelf."""

    def test_get_user_bookshelf_success(self, mock_db):
        """Test successful bookshelf retrieval."""
        with patch("app.routes.recommendation_routes.BookshelfService") as MockBookshelfService:
            mock_bookshelf_service = Mock()
            mock_item = Mock(book_id="book-1", shelf_status="read")
            mock_bookshelf_service.list_shelf.side_effect = [
                [mock_item],  # read items
                [mock_item, Mock(book_id="book-2", shelf_status="reading")]  # all items
            ]
            MockBookshelfService.return_value = mock_bookshelf_service

            result = debug_get_user_bookshelf(user_id="user-123", db=mock_db)

            assert result["user_id"] == "user-123"
            assert result["total_shelf_items"] == 2
            assert result["read_books_count"] == 1

    def test_get_user_bookshelf_error(self, mock_db):
        """Test bookshelf retrieval with error."""
        with patch("app.routes.recommendation_routes.BookshelfService") as MockBookshelfService:
            mock_bookshelf_service = Mock()
            mock_bookshelf_service.list_shelf.side_effect = Exception("DB error")
            MockBookshelfService.return_value = mock_bookshelf_service

            with pytest.raises(HTTPException) as exc_info:
                debug_get_user_bookshelf(user_id="user-123", db=mock_db)
            
            assert exc_info.value.status_code == 400


class TestRecommendContentBased:
    """Test content-based recommendation endpoint."""

    def test_recommend_content_based_success(self, mock_db):
        """Test successful content-based recommendation."""
        from app.routes.recommendation_routes import ContentBasedRequest

        with patch("app.routes.recommendation_routes.get_recommendation_engine") as MockGetEngine:
            mock_engine = Mock()
            mock_book = Mock(book_id="book-2", title="Similar Book")
            mock_engine.recommend_content_based.return_value = [
                {
                    "book": mock_book,
                    "similarity": 0.95,
                    "score": 0.95,
                    "contrast_score": None
                }
            ]
            MockGetEngine.return_value = mock_engine

            payload = ContentBasedRequest(
                user_id="user-1",
                book_id="book-1",
                rating=5,
                review_text="Great book!"
            )

            result = recommend_content_based(
                payload=payload,
                db=mock_db,
                engine=mock_engine
            )

            assert len(result) == 1
            assert result[0]["book"].book_id == "book-2"

    def test_recommend_content_based_error(self, mock_db):
        """Test content-based recommendation with error."""
        from app.routes.recommendation_routes import ContentBasedRequest

        mock_engine = Mock()
        mock_engine.recommend_content_based.side_effect = Exception("Error")

        payload = ContentBasedRequest(
            user_id="user-1",
            book_id="book-1",
            rating=5,
            review_text="Great book!"
        )

        with pytest.raises(HTTPException) as exc_info:
            recommend_content_based(
                payload=payload,
                db=mock_db,
                engine=mock_engine
            )
        
        assert exc_info.value.status_code == 400


class TestRecommendCollaborative:
    """Test collaborative recommendation endpoint."""

    def test_recommend_collaborative_success(self, mock_db):
        """Test successful collaborative recommendation."""
        from app.routes.recommendation_routes import CollaborativeRequest

        mock_engine = Mock()
        mock_book = Mock(book_id="book-3", title="Recommended Book")
        mock_engine.recommend_collaborative.return_value = [
            {
                "book": mock_book,
                "score": 0.88,
                "similarity": None
            }
        ]

        payload = CollaborativeRequest(
            user_id="user-1",
            book_id="book-1",
            review_text="Enjoyed this!"
        )

        result = recommend_collaborative(
            payload=payload,
            db=mock_db,
            engine=mock_engine
        )

        assert len(result) == 1
        assert result[0]["book"].book_id == "book-3"

    def test_recommend_collaborative_error(self, mock_db):
        """Test collaborative recommendation with error."""
        from app.routes.recommendation_routes import CollaborativeRequest

        mock_engine = Mock()
        mock_engine.recommend_collaborative.side_effect = Exception("Error")

        payload = CollaborativeRequest(
            user_id="user-1",
            book_id="book-1",
            review_text="Enjoyed this!"
        )

        with pytest.raises(HTTPException) as exc_info:
            recommend_collaborative(
                payload=payload,
                db=mock_db,
                engine=mock_engine
            )
        
        assert exc_info.value.status_code == 400
