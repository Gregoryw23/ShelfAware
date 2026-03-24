from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.chatbot_service import ChatbotService


def test_init_reads_api_key_and_stores_dependencies():
    db = object()
    recommendation_engine = object()

    with patch("app.services.chatbot_service.os.getenv", return_value="test-key"):
        service = ChatbotService(db=db, recommendation_engine=recommendation_engine)

    assert service.api_key == "test-key"
    assert service.db is db
    assert service.recommendation_engine is recommendation_engine
    assert "happy" in service.emotions


def test_detect_mood_from_message_matches_keyword():
    service = ChatbotService()

    assert service._detect_mood_from_message("I feel calm and serene today") == "peaceful"


def test_detect_mood_from_message_returns_none_when_ambiguous():
    service = ChatbotService()

    assert service._detect_mood_from_message("Recommend something interesting") is None


def test_get_user_mood_returns_default_without_db():
    service = ChatbotService(db=None)

    assert service._get_user_mood("u1") == "peaceful"


def test_get_user_mood_returns_latest_mood_from_db():
    db = MagicMock()
    db.execute.return_value.scalars.return_value.first.return_value = SimpleNamespace(mood="curious")
    service = ChatbotService(db=db)

    assert service._get_user_mood("u1") == "curious"


def test_get_user_mood_returns_default_when_no_entry_found():
    db = MagicMock()
    db.execute.return_value.scalars.return_value.first.return_value = None
    service = ChatbotService(db=db)

    assert service._get_user_mood("u1") == "peaceful"


def test_get_user_mood_returns_default_when_query_fails():
    db = MagicMock()
    db.execute.side_effect = RuntimeError("db error")
    service = ChatbotService(db=db)

    assert service._get_user_mood("u1") == "peaceful"


def test_get_mood_recommendations_returns_empty_without_engine():
    service = ChatbotService(db=object(), recommendation_engine=None)

    assert service._get_mood_recommendations("u1", "happy") == []


def test_get_mood_recommendations_returns_empty_without_user_id():
    service = ChatbotService(db=object(), recommendation_engine=MagicMock())

    assert service._get_mood_recommendations(None, "happy") == []


def test_get_mood_recommendations_maps_books_and_fallbacks():
    recommendation_engine = MagicMock()
    recommendation_engine.recommend_by_mood.return_value = [
        {
            "book": SimpleNamespace(
                book_id="b1",
                title="Book One",
                author="Author One",
                cover_image_url="http://example.com/1.jpg",
                subtitle="Subtitle",
                abstract="Abstract",
            ),
            "similarity": 0.88,
        },
        {
            "book": SimpleNamespace(book_id="b2", title="Book Two"),
            "similarity": 0.33,
        },
    ]
    service = ChatbotService(db=object(), recommendation_engine=recommendation_engine)

    books = service._get_mood_recommendations("u1", "happy")

    assert books == [
        {
            "book_id": "b1",
            "id": "b1",
            "title": "Book One",
            "author": "Author One",
            "cover_image_url": "http://example.com/1.jpg",
            "subtitle": "Subtitle",
            "abstract": "Abstract",
            "similarity": 0.88,
        },
        {
            "book_id": "b2",
            "id": "b2",
            "title": "Book Two",
            "author": "Unknown",
            "cover_image_url": None,
            "subtitle": None,
            "abstract": None,
            "similarity": 0.33,
        },
    ]
    recommendation_engine.recommend_by_mood.assert_called_once_with("u1", "happy", top_n=3)


def test_get_mood_recommendations_returns_empty_on_engine_error():
    recommendation_engine = MagicMock()
    recommendation_engine.recommend_by_mood.side_effect = RuntimeError("engine failed")
    service = ChatbotService(db=object(), recommendation_engine=recommendation_engine)

    assert service._get_mood_recommendations("u1", "happy") == []


def test_generate_response_returns_specific_message():
    service = ChatbotService()

    assert service.generate_response("happy") == "That's wonderful! Here are some joyful reads:"


def test_generate_response_returns_default_for_unknown_mood():
    service = ChatbotService()

    assert service.generate_response("unknown") == "Here are some books you might enjoy:"


def test_process_message_prefers_explicit_message_mood():
    recommendation_engine = MagicMock()
    service = ChatbotService(db=object(), recommendation_engine=recommendation_engine)
    service._get_user_mood = MagicMock(return_value="sad")
    service._get_mood_recommendations = MagicMock(return_value=[{"id": "b1"}])

    result = service.process_message("I feel cheerful today", user_id="u1")

    assert result["mood"] == "happy"
    assert result["books"] == [{"id": "b1"}]
    service._get_user_mood.assert_called_once_with("u1")
    service._get_mood_recommendations.assert_called_once_with("u1", "happy")


def test_process_message_uses_stored_user_mood_when_message_is_ambiguous():
    recommendation_engine = MagicMock()
    service = ChatbotService(db=object(), recommendation_engine=recommendation_engine)
    service._get_user_mood = MagicMock(return_value="nostalgic")
    service._get_mood_recommendations = MagicMock(return_value=[])

    result = service.process_message("Can you suggest a book?", user_id="u1")

    assert result["mood"] == "nostalgic"
    service._get_mood_recommendations.assert_called_once_with("u1", "nostalgic")


def test_process_message_falls_back_to_peaceful_without_message_or_user_mood():
    recommendation_engine = MagicMock()
    service = ChatbotService(db=None, recommendation_engine=recommendation_engine)
    service._get_mood_recommendations = MagicMock(return_value=[])

    result = service.process_message("Can you suggest a book?", user_id="u1")

    assert result["mood"] == "peaceful"
    service._get_mood_recommendations.assert_called_once_with("u1", "peaceful")


def test_process_message_skips_recommendations_when_engine_is_missing():
    service = ChatbotService(db=object(), recommendation_engine=None)
    service._get_user_mood = MagicMock(return_value="grateful")

    result = service.process_message("No clear mood here", user_id="u1")

    assert result["mood"] == "grateful"
    assert result["books"] == []
    assert len(result["follow_up_questions"]) == 3
