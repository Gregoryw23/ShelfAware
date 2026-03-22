
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.services.chatbot_service import ChatbotService
from app.dependencies.db import get_db
from app.services.mood_recommendation.recommendation_engine import RecommendationEngine
from app.services.book_service import BookService
from app.services.review_service import ReviewService
from app.services.bookshelf_service import BookshelfService

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None


class BookRecommendation(BaseModel):
    id: str
    title: str
    author: str
    similarity: float

class ChatResponse(BaseModel):
    response: str
    mood: str
    books: List[BookRecommendation]
    follow_up_questions: List[str]


def get_chatbot_service(db: Session = Depends(get_db)) -> ChatbotService:
    """Create a ChatbotService with recommendation dependencies."""
    book_service = BookService(db)
    review_service = ReviewService(db)
    bookshelf_service = BookshelfService(db)
    recommendation_engine = RecommendationEngine(
        book_service=book_service,
        review_service=review_service,
        bookshelf_service=bookshelf_service,
        db=db,
    )
    return ChatbotService(db=db, recommendation_engine=recommendation_engine)

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chatbot_service: ChatbotService = Depends(get_chatbot_service),
):
    result = chatbot_service.process_message(request.message, request.user_id)
    return result
