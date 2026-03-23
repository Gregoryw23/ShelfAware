import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class SynopsisModeration(Base):
    __tablename__ = "synopsis_moderation"

    moderation_id = Column(String, primary_key=True, default=new_uuid)
    book_id = Column(String, ForeignKey("book.book_id"), nullable=False, index=True)

    status = Column(String, nullable=False, default="pending", index=True)
    current_synopsis = Column(String, nullable=True)
    proposed_synopsis = Column(String, nullable=False)
    user_synopsis_count = Column(Integer, nullable=False, default=0)
    user_content_hash = Column(String, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    book = relationship("Book")
