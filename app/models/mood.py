import uuid, pydantic
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

# models/mood.py
class Mood(Base):
    __tablename__ = "moods"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("user.user_id"), nullable=False, index=True)
    mood = Column(String, nullable=False)
    note = Column(String, nullable=True)
    mood_date = Column(Date, nullable=False)

    user = relationship("User", back_populates="mood")
