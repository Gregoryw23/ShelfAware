from sqlalchemy import Column, Integer, String
from app.db.database import Base


class Genre(Base):
    __tablename__ = "genre"

    genre_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
