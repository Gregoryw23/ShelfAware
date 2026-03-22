from datetime import datetime
from unittest.mock import MagicMock

from app.main import app


def test_bookshelf_update_progress_success(client, mocker):
    from app.dependencies.auth import get_current_db_user

    mock_service = MagicMock()
    mock_service.update_progress.return_value = {
        "user_id": "u-1",
        "book_id": "b-1",
        "shelf_status": "currently_reading",
        "progress_percent": 50,
        "mood": "focused",
        "date_added": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "date_started": None,
        "date_finished": None,
    }

    app.dependency_overrides[get_current_db_user] = lambda: {"user_id": "u-1"}
    mocker.patch("app.routes.bookshelf.get_bookshelf_service", return_value=mock_service)
    try:
        response = client.patch(
            "/bookshelf/b-1/progress",
            json={"progress_percent": 50, "mood": "focused"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200


def test_bookshelf_update_progress_not_found(client, mocker):
    from app.dependencies.auth import get_current_db_user

    mock_service = MagicMock()
    mock_service.update_progress.side_effect = ValueError("NOT_FOUND")
    app.dependency_overrides[get_current_db_user] = lambda: {"user_id": "u-1"}
    mocker.patch("app.routes.bookshelf.get_bookshelf_service", return_value=mock_service)
    try:
        response = client.patch("/bookshelf/b-1/progress", json={"progress_percent": 20})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_bookshelf_update_progress_generic_error(client, mocker):
    from app.dependencies.auth import get_current_db_user

    mock_service = MagicMock()
    mock_service.update_progress.side_effect = ValueError("bad")
    app.dependency_overrides[get_current_db_user] = lambda: {"user_id": "u-1"}
    mocker.patch("app.routes.bookshelf.get_bookshelf_service", return_value=mock_service)
    try:
        response = client.patch("/bookshelf/b-1/progress", json={"progress_percent": 20})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
