from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class BookGenre(Base):
    __tablename__ = "book_genre"

    book_id = Column(String, ForeignKey("book.book_id"), primary_key=True)
    genre_id = Column(Integer, ForeignKey("genre.genre_id"), primary_key=True)

    book = relationship("Book", back_populates="book_genres")
    genre = relationship("Genre", back_populates="book_genres")
