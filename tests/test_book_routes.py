import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app  # Import your FastAPI app
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate, BookRead
from app.dependencies.services import get_book_service
from app.dependencies.auth import get_current_user
from app.dependencies.roles import required_admin_role
from datetime import date


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_book_service():
    """Mock BookService for testing."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def sample_book():
    """Sample book instance."""
    return Book(
        book_id="test-book-123",
        title="Test Book",
        subtitle="A Test Subtitle",
        cover_image_url="http://example.com/cover.jpg",
        abstract="This is a test book abstract.",
        page_count=300,
        published_date=date(2023, 1, 1)
    )


@pytest.fixture
def sample_book_read():
    """Sample BookRead schema."""
    return BookRead(
        book_id="test-book-123",
        title="Test Book",
        subtitle="A Test Subtitle",
        cover_image_url="http://example.com/cover.jpg",
        abstract="This is a test book abstract.",
        page_count=300,
        published_date=date(2023, 1, 1),
        created_at=None
    )


@pytest.fixture
def sample_book_create():
    """Sample BookCreate schema."""
    return BookCreate(
        title="New Test Book",
        subtitle="New Subtitle",
        cover_image_url="http://example.com/new-cover.jpg",
        abstract="New book abstract.",
        page_count=250,
        published_date=date(2024, 1, 1)
    )


@pytest.fixture
def sample_book_update():
    """Sample BookUpdate schema."""
    return BookUpdate(
        title="Updated Test Book",
        page_count=350
    )


@pytest.fixture
def mock_admin_user():
    """Mock admin user for authentication."""
    user = MagicMock()
    user.user_id = "admin-123"
    user.role = "admin"
    return user


@pytest.fixture
def mock_regular_user():
    """Mock regular user for authentication."""
    user = MagicMock()
    user.user_id = "user-123"
    user.role = "user"
    return user


class TestBookRoutes:
    """Integration tests for book CRUD routes."""

    def test_get_books_success(self, client, mock_book_service, sample_book_read):
        """Test GET /books returns list of books."""
        mock_book_service.get_books.return_value = [sample_book_read]

        with patch('app.routes.books.get_book_service', return_value=mock_book_service):
            response = client.get("/books")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["book_id"] == "test-book-123"
        assert data[0]["title"] == "Test Book"

    def test_get_book_success(self, client, mock_book_service, sample_book_read):
        """Test GET /books/{book_id} returns specific book."""
        mock_book_service.get_book.return_value = sample_book_read

        with patch('app.routes.books.get_book_service', return_value=mock_book_service):
            response = client.get("/books/test-book-123")

        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == "test-book-123"
        assert data["title"] == "Test Book"

    def test_get_book_not_found(self, client, mock_book_service):
        """Test GET /books/{book_id} returns 404 when book not found."""
        mock_book_service.get_book.return_value = None

        with patch('app.routes.books.get_book_service', return_value=mock_book_service):
            response = client.get("/books/nonexistent-book")

        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]

    @patch('app.routes.books.get_current_user')
    def test_add_book_admin_success(self, mock_get_user, client, mock_book_service, sample_book_create, sample_book_read, mock_admin_user):
        """Test POST /books creates book when user is admin."""
        mock_get_user.return_value = mock_admin_user
        mock_book_service.add_book.return_value = sample_book_read

        with patch('app.routes.books.get_book_service', return_value=mock_book_service):
            response = client.post("/books", json=sample_book_create.model_dump())

        assert response.status_code == 201
        data = response.json()
        assert data["book_id"] == "test-book-123"
        assert data["title"] == "Test Book"

    @patch('app.routes.books.get_current_user')
    def test_add_book_regular_user_forbidden(self, mock_get_user, client, mock_regular_user):
        """Test POST /books returns 403 when user is not admin."""
        mock_get_user.return_value = mock_regular_user

        response = client.post("/books", json={"title": "Test Book"})

        assert response.status_code == 403
        assert "Admin role required" in response.json()["detail"]

    @patch('app.routes.books.get_current_user')
    def test_update_book_admin_success(self, mock_get_user, client, mock_book_service, sample_book_update, sample_book_read, mock_admin_user):
        """Test PUT /books/{book_id} updates book when user is admin."""
        mock_get_user.return_value = mock_admin_user
        mock_book_service.update_book.return_value = sample_book_read

        with patch('app.routes.books.get_book_service', return_value=mock_book_service):
            response = client.put("/books/test-book-123", json=sample_book_update.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == "test-book-123"

    @patch('app.routes.books.get_current_user')
    def test_update_book_not_found(self, mock_get_user, client, mock_book_service, sample_book_update, mock_admin_user):
        """Test PUT /books/{book_id} returns 404 when book not found."""
        mock_get_user.return_value = mock_admin_user
        mock_book_service.update_book.return_value = None

        with patch('app.routes.books.get_book_service', return_value=mock_book_service):
            response = client.put("/books/nonexistent-book", json=sample_book_update.model_dump())

        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]

    @patch('app.routes.books.get_current_user')
    def test_update_book_regular_user_forbidden(self, mock_get_user, client, mock_regular_user):
        """Test PUT /books/{book_id} returns 403 when user is not admin."""
        mock_get_user.return_value = mock_regular_user

        response = client.put("/books/test-book-123", json={"title": "Updated Title"})

        assert response.status_code == 403

    @patch('app.routes.books.get_current_user')
    def test_delete_book_admin_success(self, mock_get_user, client, mock_book_service, mock_admin_user):
        """Test DELETE /books/{book_id} deletes book when user is admin."""
        mock_get_user.return_value = mock_admin_user
        mock_book_service.delete_book.return_value = True

        with patch('app.routes.books.get_book_service', return_value=mock_book_service):
            response = client.delete("/books/test-book-123")

        assert response.status_code == 200

    @patch('app.routes.books.get_current_user')
    def test_delete_book_not_found(self, mock_get_user, client, mock_book_service, mock_admin_user):
        """Test DELETE /books/{book_id} returns 404 when book not found."""
        mock_get_user.return_value = mock_admin_user
        mock_book_service.delete_book.return_value = False

        with patch('app.routes.books.get_book_service', return_value=mock_book_service):
            response = client.delete("/books/nonexistent-book")

        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]

    @patch('app.routes.books.get_current_user')
    def test_delete_book_regular_user_forbidden(self, mock_get_user, client, mock_regular_user):
        """Test DELETE /books/{book_id} returns 403 when user is not admin."""
        mock_get_user.return_value = mock_regular_user

        response = client.delete("/books/test-book-123")

        assert response.status_code == 403

    def test_add_book_validation_error(self, client):
        """Test POST /books returns 422 for invalid data."""
        # Missing required title field
        invalid_data = {"subtitle": "Test Subtitle"}

        response = client.post("/books", json=invalid_data)

        assert response.status_code == 422
        assert "title" in str(response.json())

    def test_update_book_validation_error(self, client):
        """Test PUT /books/{book_id} returns 422 for invalid data."""
        # Invalid page_count (should be positive integer)
        invalid_data = {"page_count": -1}

        response = client.put("/books/test-book-123", json=invalid_data)

        assert response.status_code == 422