from sqlalchemy import Column, Integer, String
from app.db.database import Base


class Author(Base):
    __tablename__ = "author"

    author_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
