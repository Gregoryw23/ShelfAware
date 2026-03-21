"""
Shared pytest fixtures and configuration for review tests.
This file is automatically discovered by pytest.
"""

import pytest
from fastapi.testclient import TestClient

from datetime import datetime

from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.services.review_service import ReviewService
from app.models.review import Review
from app.models.user import User
from app.models.book import Book
from app.models.mood import Mood

"""In-memory SQLite database setup for testing"""
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool,)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def mock_db():
    """Mock SQLAlchemy database session."""
    return Mock(spec=Session)

#Fresh in-memory DB for each test
@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

# FastAPI TestClient with DB override
@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

@pytest.fixture
def review_service(mock_db):
    """Create ReviewService with mocked DB."""
    return ReviewService(db=mock_db)


@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "user_id": "user-123",
        "cognito_sub": "cognito-sub-123",
        "id": "user-123",
    }


@pytest.fixture
def sample_book():
    """Sample book data."""
    return {
        "book_id": "book-456",
        "title": "Sample Book",
    }


@pytest.fixture
def sample_review():
    """Sample review object."""
    return Review(
        review_id="review-789",
        user_id="user-123",
        book_id="book-456",
        rating=5,
        title="Great Book!",
        body="This book was amazing!",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_review_low_rating():
    """Sample review with low rating."""
    return Review(
        review_id="review-790",
        user_id="user-124",
        book_id="book-456",
        rating=2,
        title="Not Great",
        body="Disappointed with this book.",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_reviews_list():
    """Sample list of reviews."""
    return [
        Review(
            review_id=f"review-{i}",
            user_id=f"user-{i}",
            book_id="book-456",
            rating=5 - (i % 5),
            title=f"Review {i}",
            body=f"This is review number {i}",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        for i in range(5)
    ]

"""Cognito mocks for auth tests"""

@pytest.fixture
def mock_cognito():
    """
    Patch the Cognito object used by the auth router.
    Adjust the patch target if your code imports it differently.
    """
    with patch("app.routers.auth.cognito_service") as mock:
        mock.register_user.return_value = {
            "UserSub": "test-sub-uuid-1234",
            "UserConfirmed": False,
        }
        mock.authenticate_user.return_value = {
            "AccessToken": "fake-access-token",
            "IdToken": "fake-id-token",
            "RefreshToken": "fake-refresh-token",
            "TokenType": "Bearer",
            "ExpiresIn": 3600,
        }
        mock.confirm_user.return_value = {
            "message": "User confirmed successfully"
        }
        mock.resend_confirmation_code.return_value = {
            "message": "Confirmation code resent"
        }
        mock.forgot_password.return_value = {
            "message": "Password reset code sent"
        }
        mock.confirm_forgot_password.return_value = {
            "message": "Password reset successful"
        }
        yield mock

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer fake-access-token"}