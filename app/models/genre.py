from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.database import Base


class Genre(Base):
    __tablename__ = "genre"

    genre_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    book_genres = relationship("BookGenre", back_populates="genre", cascade="all, delete-orphan")

    books = relationship("Book", secondary="book_genre", back_populates="genres", viewonly=True, lazy="selectin")
