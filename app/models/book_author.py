import uuid, pydantic
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class book_author(Base):
    __tablename__ = "book_author"

    book_id = Column(String, ForeignKey("book.book_id"), primary_key=True)
    author_id = Column(String, ForeignKey("author.author_id"), primary_key=True)