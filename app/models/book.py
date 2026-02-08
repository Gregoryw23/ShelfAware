import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Date
from sqlalchemy.orm import relationship

from app.db.database import Base

class Book(Base):
    __tablename__ = "book"

    book_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)

    subtitle = Column(String, nullable=True)
    cover_image_url = Column(String, nullable=True)

    abstract = Column(String, nullable=True)

    page_count = Column(Integer, nullable=True)
    published_date = Column(Date, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    bookshelves = relationship(
        "Bookshelf",
        back_populates="book",
        cascade="all, delete-orphan"
    )
