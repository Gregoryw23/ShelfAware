from fastapi.testclient import TestClient

from app.dependencies.services import get_review_service
from app.main import app
from app.models.genre import Genre


def test_books_genres_route_covers_query(db):
    from app.dependencies.db import get_db as dep_get_db

    def _override_get_db():
        yield db

    app.dependency_overrides[dep_get_db] = _override_get_db

    db.add_all([Genre(name="Fantasy"), Genre(name="Classics")])
    db.commit()

    try:
        with TestClient(app) as client:
            response = client.get("/books/genres")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data[:2] == ["Classics", "Fantasy"]
    assert data == sorted(data)


def test_get_review_service_dependency(db):
    service = get_review_service(db)
    assert service.db is db


def test_model_uuid_helpers_execute():
    from app.models.book import new_uuid as book_uuid
    from app.models.review import new_uuid as review_uuid
    from app.models.synopsis_moderation import new_uuid as mod_uuid

    assert isinstance(book_uuid(), str) and len(book_uuid()) > 0
    assert isinstance(review_uuid(), str) and len(review_uuid()) > 0
    assert isinstance(mod_uuid(), str) and len(mod_uuid()) > 0
