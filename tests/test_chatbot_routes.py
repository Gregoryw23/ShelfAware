from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.models.book import Book
from app.routes import chatbot


def make_book(book_id="b1", title="Book One"):
    return Book(book_id=book_id, title=title, created_at=datetime.now(timezone.utc).replace(tzinfo=None))


def test_get_chatbot_service_wires_dependencies():
    db = object()

    with pytest.MonkeyPatch.context() as monkeypatch:
        mock_book_service = MagicMock()
        mock_review_service = MagicMock()
        mock_bookshelf_service = MagicMock()
        mock_engine = MagicMock()
        mock_chatbot_service = MagicMock()

        monkeypatch.setattr(chatbot, "BookService", mock_book_service)
        monkeypatch.setattr(chatbot, "ReviewService", mock_review_service)
        monkeypatch.setattr(chatbot, "BookshelfService", mock_bookshelf_service)
        monkeypatch.setattr(chatbot, "RecommendationEngine", mock_engine)
        monkeypatch.setattr(chatbot, "ChatbotService", mock_chatbot_service)

        chatbot.get_chatbot_service(db)

    mock_book_service.assert_called_once_with(db)
    mock_review_service.assert_called_once_with(db)
    mock_bookshelf_service.assert_called_once_with(db)
    mock_engine.assert_called_once_with(
        book_service=mock_book_service.return_value,
        review_service=mock_review_service.return_value,
        bookshelf_service=mock_bookshelf_service.return_value,
        db=db,
    )
    mock_chatbot_service.assert_called_once_with(db=db, recommendation_engine=mock_engine.return_value)


@pytest.mark.anyio
async def test_chat_endpoint_returns_service_result():
    request = chatbot.ChatRequest(message="I feel happy", user_id="u1")
    service = MagicMock()
    service.process_message.return_value = {
        "response": "That's wonderful! Here are some joyful reads:",
        "mood": "happy",
        "books": [
            {
                "book_id": "b1",
                "id": "b1",
                "title": "Book One",
                "author": "Unknown",
                "similarity": 0.9,
                "cover_image_url": None,
                "subtitle": None,
                "abstract": None,
            }
        ],
        "follow_up_questions": ["Would you like books in a different mood?"],
    }

    result = await chatbot.chat(request, chatbot_service=service)

    assert result["mood"] == "happy"
    assert result["books"][0]["id"] == "b1"
    service.process_message.assert_called_once_with("I feel happy", "u1")


def test_chat_models_accept_expected_payloads():
    book = make_book()

    response = chatbot.ChatResponse(
        response="Hello",
        mood="happy",
        books=[
            chatbot.BookRecommendation(
                book_id=book.book_id,
                id=book.book_id,
                title=book.title,
                author="Unknown",
                similarity=0.7,
            )
        ],
        follow_up_questions=["Want more recommendations?"],
    )

    assert response.books[0].title == "Book One"
    assert response.follow_up_questions == ["Want more recommendations?"]
