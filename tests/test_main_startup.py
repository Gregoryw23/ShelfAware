import pytest
from unittest.mock import Mock, patch, AsyncMock
import logging

from app.main import app, lifespan


class TestSchedulerSync:
    """Test scheduler sync endpoint."""

    def test_trigger_scheduler_sync_success(self):
        """Test manual scheduler sync endpoint success."""
        from fastapi.testclient import TestClient
        
        with patch("app.main.SynopsisScheduler") as MockScheduler:
            MockScheduler.add_manual_job.return_value = {"status": "success", "message": "Job added"}
            
            client = TestClient(app)
            response = client.post("/admin/trigger-scheduler-sync")
            
            assert response.status_code == 200
            assert response.json()["status"] == "success"

    def test_trigger_scheduler_sync_scheduler_none(self):
        """Test manual scheduler sync when scheduler is None (line 52-53)."""
        from fastapi.testclient import TestClient
        
        with patch("app.main.SynopsisScheduler", None):
            client = TestClient(app)
            response = client.post("/admin/trigger-scheduler-sync")
            
            # Should handle gracefully when scheduler is None
            assert response.status_code == 200
            assert "error" in response.json()["status"].lower() or "scheduler" in response.json()["message"].lower()


class TestApplicationStartup:
    """Test application initialization and routes."""

    def test_app_is_created(self):
        """Test that FastAPI app is created."""
        assert app is not None
        assert app.title == "ShelfAware API"

    def test_app_has_routers(self):
        """Test that all expected routers are included."""
        # Get all registered routes
        routes = [route.path for route in app.routes]
        
        # Check that key prefixes are included
        assert any("/auth" in route for route in routes)
        assert any("/admin" in route for route in routes)
        assert any("/books" in route for route in routes)
        assert any("/bookshelf" in route for route in routes)

    def test_home_endpoint(self):
        """Test home endpoint."""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Welcome to ShelfAware"

    def test_favicon_endpoint(self):
        """Test favicon endpoint."""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/favicon.ico")
        
        # favicon.ico should return no content (204) or empty (200)
        assert response.status_code in [200, 204]

    def test_cors_middleware_configured(self):
        """Test that CORS middleware is configured."""
        # Get middleware stack
        middleware_classes = [type(m.cls).__name__ for m in app.user_middleware]
        
        # Check that CORSMiddleware is in the stack
        # The middleware class name should contain CORS
        has_cors = any("CORS" in cls_name or "cors" in str(m.cls).lower() for cls_name, m in zip(middleware_classes, app.user_middleware))
        assert has_cors or any("CORSMiddleware" in str(m) for m in middleware_classes)
