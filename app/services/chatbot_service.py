from typing import Dict, List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload
from app.models.book import Book
from app.models.genre import Genre

class ChatbotService:
    def __init__(self, db: Session):
        self.db = db

        self.emotions = [
            "happy", "sad", "angry", "excited", "scared", "romantic", 
            "suspenseful", "dark", "hopeful", "nostalgic", "peaceful", 
            "curious", "empowered", "lonely", "grateful", "confused", 
            "inspired", "amused", "moved", "adventurous", "reflective", 
            "whimsical", "heartbroken", "triumphant"
        ]

        self.mood_genre_keywords = {
            "happy": ["comedy", "humor", "fiction", "feel-good"],
            "sad": ["biography", "memoir", "self-help", "inspir"],
            "angry": ["self-help", "psychology", "mindfulness"],
            "excited": ["thriller", "adventure", "action", "fantasy"],
            "scared": ["horror", "thriller", "mystery"],
            "romantic": ["romance", "drama"],
            "suspenseful": ["thriller", "mystery", "crime"],
            "dark": ["horror", "psychological", "dystopian"],
            "hopeful": ["self-help", "inspir", "biography"],
            "nostalgic": ["classic", "historical", "memoir"],
            "peaceful": ["poetry", "philosophy", "self-help"],
            "curious": ["science", "history", "non-fiction", "mystery"],
            "empowered": ["biography", "self-help", "leadership"],
            "lonely": ["memoir", "self-help", "fiction"],
            "grateful": ["memoir", "spiritual", "self-help"],
            "confused": ["philosophy", "psychology", "self-help"],
            "inspired": ["biography", "self-help", "inspir"],
            "amused": ["comedy", "humor"],
            "moved": ["drama", "memoir", "fiction"],
            "adventurous": ["adventure", "fantasy", "science fiction", "thriller"],
            "reflective": ["philosophy", "memoir", "classic"],
            "whimsical": ["fantasy", "magical", "fiction"],
            "heartbroken": ["romance", "self-help", "memoir"],
            "triumphant": ["biography", "self-help", "history"],
        }
    
    def detect_mood(self, message: str) -> List[str]:
        message_lower = message.lower()
        
        mood_keywords = {
            "happy": ["happy", "joy", "great", "wonderful"],
            "sad": ["sad", "depressed", "down", "unhappy", "lonely"],
            "angry": ["angry", "mad", "frustrated", "annoyed"],
            "excited": ["excited", "thrilled", "pumped"],
            "romantic": ["love", "romantic", "romance"],
            "adventurous": ["adventure", "exciting", "thrilling"]
        }
        
        for mood, keywords in mood_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return [mood]
        
        return ["peaceful"]
    
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

    def get_recommended_books(self, mood: str, limit: int = 3) -> List[Dict]:
        """Return DB-backed recommendations using mood-to-genre keyword matching."""
        keywords = self.mood_genre_keywords.get(mood, ["fiction", "self-help", "mystery"])

        query = self.db.query(Book).options(selectinload(Book.genres))

        genre_filters = [Book.genres.any(Genre.name.ilike(f"%{kw}%")) for kw in keywords]

        if genre_filters:
            matched_books = (
                query.filter(or_(*genre_filters))
                .order_by(Book.created_at.desc())
                .limit(limit)
                .all()
            )
        else:
            matched_books = []

        if len(matched_books) < limit:
            matched_ids = {book.book_id for book in matched_books}
            fallback_books = (
                query.filter(~Book.book_id.in_(matched_ids) if matched_ids else True)
                .order_by(Book.created_at.desc())
                .limit(limit - len(matched_books))
                .all()
            )
            matched_books.extend(fallback_books)

        results = []
        for book in matched_books:
            results.append(
                {
                    "book_id": book.book_id,
                    "title": book.title,
                    "subtitle": book.subtitle,
                    "abstract": book.abstract,
                    "cover_image_url": book.cover_image_url,
                    "genres": [genre.name for genre in (book.genres or [])],
                }
            )

        return results
    
    def process_message(self, message: str, user_id: Optional[str] = None) -> Dict:
        moods = self.detect_mood(message)
        primary_mood = moods[0]
        
        response_text = self.generate_response(primary_mood)
        
        books = self.get_recommended_books(primary_mood)
        
        follow_ups = [
            "Would you like books in a different mood?",
            "Tell me more about what you're looking for",
            "Want more recommendations?"
        ]
        
        return {
            "response": response_text,
            "mood": primary_mood,
            "books": books,
            "follow_up_questions": follow_ups
        }
