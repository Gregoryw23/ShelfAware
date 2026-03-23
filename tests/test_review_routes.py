import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os
from datetime import datetime

from app.main import app
from app.services.review_service import ReviewService
from app.dependencies.auth import get_current_user



@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        "DATABASE_URL": "sqlite:///test.db",
    }):
        yield


@pytest.fixture
def mock_review_service():
    """Mock ReviewService for route testing."""
    with patch('app.routes.review.ReviewService') as MockService:
        mock_instance = Mock(spec=ReviewService)
        MockService.return_value = mock_instance
        yield MockService


@pytest.fixture
def client(mock_review_service):
    """Test client with mocked auth and review service."""
    async def mock_get_current_user():
        return {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "role": "user"
        }
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ============================================================================
# TESTS: POST /reviews/books/{book_id}
# ============================================================================

class TestCreateReviewEndpoint:
    """Tests for POST /reviews/books/{book_id}"""

    def test_create_review_success(self, client, mock_review_service):
        """Test successfully creating a review."""
        # Arrange
        mock_instance = mock_review_service.return_value
        mock_instance.add_review.return_value = {
            "review_id": "review-789",
            "book_id": "book-456",
            "user_id": "user-123",
            "rating": 5,
            "comment": "Great book!",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
                
        payload = {"rating": 5, "comment": "Great book!"}
        
        # Act
        response = client.post("/reviews/books/book-456", json=payload)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Great book!"
        mock_instance.add_review.assert_called_once()

    def test_create_review_invalid_rating_zero(self, client, mock_review_service):
        """Test creating review with invalid rating."""
        # Arrange
        payload = {"rating": 0, "comment": "Bad"}
        
        # Act
        response = client.post("/reviews/books/book-456", json=payload)
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_create_review_missing_rating(self, client, mock_review_service):
        """Test creating review without required rating."""
        # Arrange
        payload = {"comment": "No rating"}
        
        # Act
        response = client.post("/reviews/books/book-456", json=payload)
        
        # Assert
        assert response.status_code == 422

    def test_create_review_book_not_found(self, client, mock_review_service):
        """Test creating review when book doesn't exist."""
        # Arrange
        from fastapi import HTTPException
        mock_instance = mock_review_service.return_value
        mock_instance.add_review.side_effect = HTTPException(
            status_code=404,
            detail="Book not found"
        )
        
        payload = {"rating": 5, "comment": "Test"}
        
        # Act
        response = client.post("/reviews/books/nonexistent", json=payload)
        
        # Assert
        assert response.status_code == 404

    def test_create_review_duplicate(self, client, mock_review_service):
        """Test creating duplicate review."""
        # Arrange
        from fastapi import HTTPException
        mock_instance = mock_review_service.return_value
        mock_instance.add_review.side_effect = HTTPException(
            status_code=409,
            detail="You have already reviewed this book"
        )
        
        payload = {"rating": 5, "comment": "Test"}
        
        # Act
        response = client.post("/reviews/books/book-456", json=payload)
        
        # Assert
        assert response.status_code == 409
        assert "already reviewed" in response.json()["detail"].lower()


# ============================================================================
# TESTS: GET /reviews/book/{book_id}
# ============================================================================

class TestGetReviewsForBookEndpoint:
    """Tests for GET /reviews/book/{book_id}"""

    def test_get_reviews_success(self, client, mock_review_service):
        """Test retrieving reviews for a book."""
        # Arrange
        mock_instance = mock_review_service.return_value
        mock_instance.get_reviews_by_book_id.return_value = [
            {
                "review_id": "r1",
                "book_id": "book-456",
                "user_id": "user-123",
                "rating": 5,
                "comment": "Great!",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "review_id": "r2",
                "book_id": "book-456",
                "user_id": "user-456",
                "rating": 4,
                "comment": "Good!",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        # Act
        response = client.get("/reviews/book/book-456")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["rating"] == 5

    def test_get_reviews_empty(self, client, mock_review_service):
        """Test retrieving reviews when none exist."""
        # Arrange
        mock_instance = mock_review_service.return_value
        mock_instance.get_reviews_by_book_id.return_value = []
        
        # Act
        response = client.get("/reviews/book/book-456")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == []

    def test_get_reviews_with_pagination(self, client, mock_review_service):
        """Test pagination parameters."""
        # Arrange
        mock_instance = mock_review_service.return_value
        mock_instance.get_reviews_by_book_id.return_value = [
            {
                "review_id": "r1",
                "book_id": "book-456",
                "user_id": "user-123",
                "rating": 5,
                "comment": "Great!",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
                
        # Act
        response = client.get("/reviews/book/book-456?limit=5&offset=0&newest_first=true")
        
        # Assert
        assert response.status_code == 200
        mock_instance.get_reviews_by_book_id.assert_called_once()


# ============================================================================
# TESTS: PUT /reviews/{review_id}
# ============================================================================

class TestUpdateReviewEndpoint:
    """Tests for PUT /reviews/{review_id}"""

    def test_update_review_success(self, client, mock_review_service):
        """Test updating a review."""
        # Arrange
        mock_instance = mock_review_service.return_value
        mock_instance.update_review.return_value = {
            "review_id": "review-789",
            "book_id": "book-456",
            "user_id": "user-123",
            "rating": 4,
            "comment": "Updated comment",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        payload = {"rating": 4, "comment": "Updated comment"}
        
        # Act
        response = client.put("/reviews/review-789", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 4

    def test_update_review_not_authorized(self, client, mock_review_service):
        """Test updating review by non-owner."""
        # Arrange
        from fastapi import HTTPException
        mock_instance = mock_review_service.return_value
        mock_instance.update_review.side_effect = HTTPException(
            status_code=403,
            detail="Not authorized to update this review"
        )
        
        payload = {"rating": 1}
        
        # Act
        response = client.put("/reviews/review-789", json=payload)
        
        # Assert
        assert response.status_code == 403

    def test_update_review_not_found(self, client, mock_review_service):
        """Test updating non-existent review."""
        # Arrange
        from fastapi import HTTPException
        mock_instance = mock_review_service.return_value
        mock_instance.update_review.side_effect = HTTPException(
            status_code=404,
            detail="Review not found"
        )
        
        payload = {"rating": 5}
        
        # Act
        response = client.put("/reviews/nonexistent", json=payload)
        
        # Assert
        assert response.status_code == 404


# ============================================================================
# TESTS: DELETE /reviews/{review_id}
# ============================================================================

class TestDeleteReviewEndpoint:
    """Tests for DELETE /reviews/{review_id}"""

    def test_delete_review_success(self, client, mock_review_service):
        """Test deleting a review."""
        # Arrange
        mock_instance = mock_review_service.return_value
        mock_instance.delete_review.return_value = None
        
        # Act
        response = client.delete("/reviews/review-789")
        
        # Assert
        assert response.status_code == 204
        mock_instance.delete_review.assert_called_once()

    def test_delete_review_not_authorized(self, client, mock_review_service):
        """Test deleting review by non-owner."""
        # Arrange
        from fastapi import HTTPException
        mock_instance = mock_review_service.return_value
        mock_instance.delete_review.side_effect = HTTPException(
            status_code=403,
            detail="Not authorized"
        )
        
        # Act
        response = client.delete("/reviews/review-789")
        
        # Assert
        assert response.status_code == 403

    def test_delete_review_not_found(self, client, mock_review_service):
        """Test deleting non-existent review."""
        # Arrange
        from fastapi import HTTPException
        mock_instance = mock_review_service.return_value
        mock_instance.delete_review.side_effect = HTTPException(
            status_code=404,
            detail="Review not found"
        )
        
        # Act
        response = client.delete("/reviews/nonexistent")
        
        # Assert
        assert response.status_code == 404


# ============================================================================
# TESTS: GET /reviews/{review_id}
# ============================================================================

class TestGetReviewEndpoint:
    """Tests for GET /reviews/{review_id} — covers lines 111-112"""

    def test_get_review_success(self, client, mock_review_service):
        """Lines 111-112: GET /{review_id} returns a single review."""
        # Arrange
        from unittest.mock import MagicMock
        mock_instance = mock_review_service.return_value

        mock_review = MagicMock()
        mock_review.review_id = "review-789"
        mock_review.book_id = "book-456"
        mock_review.user_id = "user-123"
        mock_review.rating = 5
        mock_review.body = "Great book!"
        mock_review.title = "Great!"
        mock_review.comment = "Great book!"
        mock_review.created_at = datetime.now()
        mock_review.updated_at = datetime.now()

        mock_instance._get_review_or_404.return_value = mock_review

        # Act
        response = client.get("/reviews/review-789")

        # Assert
        assert response.status_code == 200
        mock_instance._get_review_or_404.assert_called_once_with("review-789")


    def test_get_review_not_found(self, client, mock_review_service):
        """Lines 111-112: GET /{review_id} raises 404 when not found."""
        # Arrange
        from fastapi import HTTPException
        mock_instance = mock_review_service.return_value
        mock_instance._get_review_or_404.side_effect = HTTPException(
            status_code=404,
            detail="Review not found"
        )

        # Act
        response = client.get("/reviews/nonexistent-review")

        # Assert
        assert response.status_code == 404
        assert "Review not found" in response.json()["detail"]



# ============================================================================
# TESTS: resolve_user_id fallback 
# ============================================================================

class TestResolveUserIdFallback:

    @pytest.fixture
    def client_no_user_id(self, mock_review_service):
        """Client where token has NO user_id — forces cognito fallback path."""
        async def mock_get_current_user():
            return {}  # empty — no user_id, no sub

        app.dependency_overrides[get_current_user] = mock_get_current_user
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()

    @pytest.fixture
    def client_with_sub_only(self, mock_review_service):
        """Client where token has cognito_sub but no user_id."""
        async def mock_get_current_user():
            return {"cognito_sub": "cognito-abc-123"}  # no user_id

        app.dependency_overrides[get_current_user] = mock_get_current_user
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()

    def test_resolve_user_id_no_user_id_no_sub_raises_401(self, client_no_user_id):
        # Act
        response = client_no_user_id.post(
            "/reviews/books/book-456",
            json={"rating": 5, "comment": "test"}
        )

        # Assert
        assert response.status_code == 401
        assert "missing user_id/sub" in response.json()["detail"]

    def test_resolve_user_id_sub_user_not_in_db_raises_401(self, client_with_sub_only, mock_review_service):
        # Arrange — override get_db to return a mock db where user lookup returns None
        from app.dependencies.db import get_db
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        app.dependency_overrides[get_db] = lambda: mock_db

        # Act
        response = client_with_sub_only.post(
            "/reviews/books/book-456",
            json={"rating": 5, "comment": "test"}
        )

        app.dependency_overrides.pop(get_db, None)

        # Assert
        assert response.status_code == 401
        assert "not found in database" in response.json()["detail"]


    def test_resolve_user_id_via_cognito_sub_success(self, client_with_sub_only, mock_review_service):
        # Arrange
        from app.dependencies.db import get_db
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.user_id = "user-123"

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        mock_review = MagicMock()
        mock_review.review_id = "review-789"
        mock_review.book_id = "book-456"
        mock_review.user_id = "user-123"
        mock_review.rating = 5
        mock_review.body = "Great!"
        mock_review.title = "Great!"
        mock_review.comment = "Great!"
        mock_review.created_at = datetime.now()
        mock_review.updated_at = datetime.now()

        mock_instance = mock_review_service.return_value
        mock_instance.add_review.return_value = mock_review

        app.dependency_overrides[get_db] = lambda: mock_db

        # Act
        response = client_with_sub_only.post(
            "/reviews/books/book-456",
            json={"rating": 5, "comment": "test"}
        )

        app.dependency_overrides.pop(get_db, None)

        # Assert — got past auth, service was called
        assert response.status_code != 401
        mock_instance.add_review.assert_called_once()
