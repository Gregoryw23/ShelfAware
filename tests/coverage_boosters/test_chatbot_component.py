from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.routes.chatbot import get_chatbot_service


def test_chatbot_service_factory_returns_service(db):
    service = get_chatbot_service(db)
    assert service.db is db


def test_chatbot_route_covers_chat_function():
    fake_service = MagicMock()
    fake_service.process_message.return_value = {
        "response": "Hello",
        "mood": "neutral",
        "books": [],
        "follow_up_questions": [],
    }

    from app.routes.chatbot import get_chatbot_service as dep

    app.dependency_overrides[dep] = lambda: fake_service
    try:
        with TestClient(app) as client:
            response = client.post("/api/chatbot/chat", json={"message": "hi", "user_id": "u1"})
        assert response.status_code == 200
        assert response.json()["response"] == "Hello"
    finally:
        app.dependency_overrides.clear()
