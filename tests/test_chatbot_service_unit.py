from datetime import date
from types import SimpleNamespace

from app.models.mood import Mood
from app.services.chatbot_service import ChatbotService


class _Engine:
    def __init__(self, recommendations=None, should_raise=False):
        self.recommendations = recommendations or []
        self.should_raise = should_raise

    def recommend_by_mood(self, user_id, mood, top_n=3):
        if self.should_raise:
            raise RuntimeError("engine error")
        return self.recommendations


class _FailingDB:
    def execute(self, _stmt):
        raise RuntimeError("db fail")


def test_detect_mood_from_message():
    svc = ChatbotService()
    assert svc._detect_mood_from_message("I feel joyful and cheerful today") == "happy"
    assert svc._detect_mood_from_message("No keywords here") is None


def test_get_user_mood_paths(db):
    svc_no_db = ChatbotService()
    assert svc_no_db._get_user_mood("u1") == "peaceful"

    mood = Mood(user_id="u1", mood="nostalgic", mood_date=date(2026, 3, 21))
    db.add(mood)
    db.commit()

    svc = ChatbotService(db=db)
    assert svc._get_user_mood("u1") == "nostalgic"

    failing = ChatbotService(db=_FailingDB())
    assert failing._get_user_mood("u1") == "peaceful"


def test_get_mood_recommendations_paths():
    svc_no_engine = ChatbotService()
    assert svc_no_engine._get_mood_recommendations("u1", "happy") == []

    svc_no_user = ChatbotService(recommendation_engine=_Engine())
    assert svc_no_user._get_mood_recommendations("", "happy") == []

    rec_book = SimpleNamespace(
        book_id="b1",
        title="Book One",
        author="Author A",
        cover_image_url="http://x",
        subtitle="Sub",
        abstract="Abs",
    )
    engine_ok = _Engine(recommendations=[{"book": rec_book, "similarity": 0.7}])
    svc_ok = ChatbotService(recommendation_engine=engine_ok)
    out = svc_ok._get_mood_recommendations("u1", "happy")
    assert out[0]["book_id"] == "b1"
    assert out[0]["id"] == "b1"
    assert out[0]["title"] == "Book One"
    assert out[0]["author"] == "Author A"
    assert out[0]["similarity"] == 0.7

    svc_err = ChatbotService(recommendation_engine=_Engine(should_raise=True))
    assert svc_err._get_mood_recommendations("u1", "happy") == []


def test_generate_response_default():
    svc = ChatbotService()
    assert "joyful" in svc.generate_response("happy").lower()
    assert svc.generate_response("unknown") == "Here are some books you might enjoy:"


def test_process_message_mood_priority_and_books(db):
    mood = Mood(user_id="u1", mood="sad", mood_date=date(2026, 3, 21))
    db.add(mood)
    db.commit()

    rec_book = SimpleNamespace(book_id="b2", title="Book Two")
    engine = _Engine(recommendations=[{"book": rec_book, "similarity": 0.9}])
    svc = ChatbotService(db=db, recommendation_engine=engine)

    explicit = svc.process_message("I am thrilled and excited", user_id="u1")
    assert explicit["mood"] == "excited"
    assert explicit["books"][0]["book_id"] == "b2"
    assert len(explicit["follow_up_questions"]) == 3

    implicit = svc.process_message("hello there", user_id="u1")
    assert implicit["mood"] == "sad"

    fallback = ChatbotService().process_message("hello there")
    assert fallback["mood"] == "peaceful"
    assert fallback["books"] == []
