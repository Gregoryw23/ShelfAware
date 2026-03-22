import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.routes.admin import (
    generate_community_reviews,
    accept_synopsis_moderation,
    reject_synopsis_moderation,
)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


class TestGenerateCommunityReviews:
    """Test community review generation endpoint."""

    def test_generate_reviews_success(self, client):
        """Test successful review generation."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
            with patch("app.routes.admin.SynopsisSyncService") as MockService:
                mock_service = Mock()
                mock_service.generate_all_community_reviews.return_value = {
                    "status": "success",
                    "timestamp": "2026-03-23T00:00:00",
                    "total_books_processed": 5,
                    "updated": 3,
                    "skipped": 2,
                    "errors": []
                }
                MockService.return_value = mock_service

                response = client.post("/admin/generate-community-reviews")
                assert response.status_code == 200
                assert response.json()["status"] == "success"

    def test_generate_reviews_missing_api_key(self, client):
        """Test review generation with missing OPENAI_API_KEY (line 60-62)."""
        with patch.dict("os.environ", {}, clear=True):
            response = client.post("/admin/generate-community-reviews")
            # The function should return an error response
            assert response.status_code == 500
            assert "not configured" in response.json()["detail"].lower() or "OPENAI_API_KEY" in response.json()["detail"]

    def test_generate_reviews_service_error(self, client):
        """Test review generation with service error."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
            with patch("app.routes.admin.SynopsisSyncService") as MockService:
                mock_service = Mock()
                mock_service.generate_all_community_reviews.side_effect = Exception("Service error")
                MockService.return_value = mock_service

                response = client.post("/admin/generate-community-reviews")
                assert response.status_code == 500


class TestAcceptSynopsisModerationItem:
    """Test accept synopsis moderation endpoint."""

    def test_accept_moderation_success(self, mock_db):
        """Test successful moderation acceptance."""
        with patch("app.routes.admin.SynopsisSyncService") as MockService:
            mock_service = Mock()
            mock_service.accept_moderation_item.return_value = {"accepted": True}
            MockService.return_value = mock_service

            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
                result = accept_synopsis_moderation(
                    moderation_id="mod-123",
                    db=mock_db
                )

                assert result["status"] == "success"
                mock_service.accept_moderation_item.assert_called_once_with(mock_db, "mod-123")

    def test_accept_moderation_not_found(self, mock_db):
        """Test accept moderation with item not found (line 87-89)."""
        with patch("app.routes.admin.SynopsisSyncService") as MockService:
            mock_service = Mock()
            mock_service.accept_moderation_item.side_effect = ValueError("Moderation item not found")
            MockService.return_value = mock_service

            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
                with pytest.raises(HTTPException) as exc_info:
                    accept_synopsis_moderation(
                        moderation_id="nonexistent",
                        db=mock_db
                    )
                
                assert exc_info.value.status_code == 404

    def test_accept_moderation_service_error(self, mock_db):
        """Test accept moderation with service error."""
        with patch("app.routes.admin.SynopsisSyncService") as MockService:
            mock_service = Mock()
            mock_service.accept_moderation_item.side_effect = Exception("DB error")
            MockService.return_value = mock_service

            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
                with pytest.raises(HTTPException) as exc_info:
                    accept_synopsis_moderation(
                        moderation_id="mod-123",
                        db=mock_db
                    )
                
                assert exc_info.value.status_code == 500


class TestRejectSynopsisModerationItem:
    """Test reject synopsis moderation endpoint."""

    def test_reject_moderation_success(self, mock_db):
        """Test successful moderation rejection."""
        with patch("app.routes.admin.SynopsisSyncService") as MockService:
            mock_service = Mock()
            mock_service.reject_moderation_item.return_value = {"rejected": True}
            MockService.return_value = mock_service

            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
                result = reject_synopsis_moderation(
                    moderation_id="mod-123",
                    db=mock_db
                )

                assert result["status"] == "success"
                mock_service.reject_moderation_item.assert_called_once_with(mock_db, "mod-123")

    def test_reject_moderation_not_found(self, mock_db):
        """Test reject moderation with item not found (line 100-102)."""
        with patch("app.routes.admin.SynopsisSyncService") as MockService:
            mock_service = Mock()
            mock_service.reject_moderation_item.side_effect = ValueError("Moderation item not found")
            MockService.return_value = mock_service

            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
                with pytest.raises(HTTPException) as exc_info:
                    reject_synopsis_moderation(
                        moderation_id="nonexistent",
                        db=mock_db
                    )
                
                assert exc_info.value.status_code == 404

    def test_reject_moderation_service_error(self, mock_db):
        """Test reject moderation with service error."""
        with patch("app.routes.admin.SynopsisSyncService") as MockService:
            mock_service = Mock()
            mock_service.reject_moderation_item.side_effect = Exception("DB error")
            MockService.return_value = mock_service

            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
                with pytest.raises(HTTPException) as exc_info:
                    reject_synopsis_moderation(
                        moderation_id="mod-123",
                        db=mock_db
                    )
                
                assert exc_info.value.status_code == 500


class TestListSynopsisModerationWithError:
    """Test list synopsis moderation error handling."""

    def test_list_moderation_error(self, mock_db):
        """Test list moderation with service error (line 113-115)."""
        from app.routes.admin import list_synopsis_moderation
        
        with patch("app.routes.admin.SynopsisSyncService") as MockService:
            mock_service = Mock()
            mock_service.list_moderation_items.side_effect = Exception("DB error")
            MockService.return_value = mock_service

            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}):
                with pytest.raises(HTTPException) as exc_info:
                    list_synopsis_moderation(
                        status="pending",
                        db=mock_db
                    )
                
                assert exc_info.value.status_code == 500
