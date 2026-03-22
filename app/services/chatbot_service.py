from typing import Dict, List, Optional
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mood import Mood
from app.services.mood_recommendation.recommendation_engine import RecommendationEngine

class ChatbotService:
    def __init__(
        self,
        db: Optional[Session] = None,
        recommendation_engine: Optional[RecommendationEngine] = None,
    ):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.db = db
        self.recommendation_engine = recommendation_engine

        self.emotions = [
            "happy", "sad", "angry", "excited", "scared", "romantic", 
            "suspenseful", "dark", "hopeful", "nostalgic", "peaceful", 
            "curious", "empowered", "lonely", "grateful", "confused", 
            "inspired", "amused", "moved", "adventurous", "reflective", 
            "whimsical", "heartbroken", "triumphant"
        ]

    def _detect_mood_from_message(self, message: str) -> Optional[str]:
        message_lower = message.lower()

        mood_keywords = {
            "happy": ["happy", "joy", "great", "wonderful", "delighted", "cheerful"],
            "sad": ["sad", "depressed", "down", "unhappy", "lonely"],
            "angry": ["angry", "mad", "frustrated", "annoyed"],
            "excited": ["excited", "thrilled", "pumped", "energized"],
            "romantic": ["love", "romantic", "romance", "lovely", "passionate"],
            "adventurous": ["adventure", "exciting", "thrilling", "journey"],
            "peaceful": ["peaceful", "calm", "serene", "tranquil"],
            "suspenseful": ["suspense", "mystery", "tense", "cliffhanger"],
            "dark": ["dark", "grim", "eerie", "sinister"],
            "hopeful": ["hope", "optimistic", "inspiring"],
            "nostalgic": ["nostalgia", "memories", "reminiscent"],
            "curious": ["curious", "intriguing", "mysterious", "fascinating"],
            "empowered": ["empowered", "strong", "courageous"],
            "lonely": ["lonely", "alone", "isolated"],
            "grateful": ["grateful", "thankful", "appreciative"],
            "confused": ["confused", "uncertain", "lost", "perplexed"],
            "inspired": ["inspired", "motivated", "creative"],
            "amused": ["amused", "funny", "humorous", "entertaining"],
            "moved": ["moved", "touching", "emotional"],
            "reflective": ["reflective", "thoughtful", "contemplative"],
            "whimsical": ["whimsical", "magical", "fantastical"],
            "heartbroken": ["heartbroken", "broken", "suffering"],
            "triumphant": ["triumphant", "victorious", "celebrating"],
        }

        for mood, keywords in mood_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return mood

        return None

    def _get_user_mood(self, user_id: str) -> str:
        """Get the user's most recent mood from the database."""
        if not self.db:
            return "peaceful"

        try:
            stmt = select(Mood).where(Mood.user_id == user_id).order_by(Mood.mood_date.desc())
            mood_entry = self.db.execute(stmt).scalars().first()

            if mood_entry:
                return mood_entry.mood
        except Exception as e:
            print(f"Error fetching user mood: {e}")

        return "peaceful"

    def _get_mood_recommendations(self, user_id: str, mood: str) -> List[Dict]:
        """Get book recommendations based on mood."""
        if not self.recommendation_engine or not user_id:
            return []

        try:
            recommendations = self.recommendation_engine.recommend_by_mood(user_id, mood, top_n=3)
            books = []
            for rec in recommendations:
                book = rec["book"]
                books.append(
                    {
                        "id": book.book_id,
                        "title": getattr(book, "title", "Unknown"),
                        "author": getattr(book, "author", "Unknown"),
                        "similarity": rec.get("similarity", 0.0),
                    }
                )

            return books
        except Exception as e:
            print(f"Error getting mood recommendations: {e}")
            return []
    
    def generate_response(self, mood: str) -> str:
        responses = {
            "happy": "That's wonderful! Here are some joyful reads:",
            "sad": "I understand you're feeling down. Here are some uplifting books:",
            "angry": "I hear you. These books might help process those feelings:",
            "excited": "Love the energy! These thrilling reads match your vibe:",
            "scared": "Looking for something that captures that feeling? Try these:",
            "romantic": "Looking for romance? I have lovely suggestions:",
            "suspenseful": "Want something gripping? These will keep you on edge:",
            "dark": "In the mood for something intense? These are perfect:",
            "hopeful": "Here are some inspiring, hopeful stories:",
            "nostalgic": "These books will take you down memory lane:",
            "peaceful": "Here are some calming, peaceful reads:",
            "curious": "These fascinating books will satisfy your curiosity:",
            "empowered": "Here are some empowering, strong stories:",
            "lonely": "I understand. These books offer comfort and connection:",
            "grateful": "Here are some heartwarming, appreciative reads:",
            "confused": "These thought-provoking books might help:",
            "inspired": "Here are some inspirational reads:",
            "amused": "Want something fun? These will make you laugh:",
            "moved": "Here are some deeply moving stories:",
            "adventurous": "Ready for adventure? These will take you on a journey:",
            "reflective": "These contemplative books are perfect for reflection:",
            "whimsical": "Here are some delightfully whimsical reads:",
            "heartbroken": "I'm sorry you're hurting. These books offer solace:",
            "triumphant": "Celebrate with these triumphant stories:"
        }
        return responses.get(mood, "Here are some books you might enjoy:")

    def process_message(self, message: str, user_id: Optional[str] = None) -> Dict:
        # Determine mood candidates: message-based (explicit intent) and stored
        # user mood (persistent preference)
        message_mood = self._detect_mood_from_message(message)
        user_mood = self._get_user_mood(user_id) if user_id and self.db else None

        # Prioritize explicit message intent if it exists; otherwise use stored
        # mood; fallback to peaceful.
        mood = message_mood or user_mood or "peaceful"

        # If the message is ambiguous and user mood is known, keep the user's
        # mood to avoid unexpected shifts.
        if message_mood is None and user_mood:
            mood = user_mood

        response_text = self.generate_response(mood)

        books = self._get_mood_recommendations(user_id, mood) if self.recommendation_engine else []

        follow_ups = [
            "Would you like books in a different mood?",
            "Tell me more about what you're looking for",
            "Want more recommendations?"
        ]

        return {
            "response": response_text,
            "mood": mood,
            "books": books,
            "follow_up_questions": follow_ups
        }
