from sqlalchemy import Column, String, Integer, ForeignKey
from app.db.database import Base


class book_genre(Base):
    __tablename__ = "book_genre"

    book_id = Column(String, ForeignKey("book.book_id"), primary_key=True)
    genre_id = Column(Integer, ForeignKey("genre.genre_id"), primary_key=True)
