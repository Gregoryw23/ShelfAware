import uuid, pydantic
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

# models/mood.py
class Mood(Base):
    __tablename__ = "moods"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.Users_id"), nullable=False)
    mood = Column(String, nullable=False)
    note = Column(String, nullable=True)
    mood_date = Column(Date, nullable=False)

    user = relationship("User", back_populates="moods")
