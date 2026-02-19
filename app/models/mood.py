from sqlalchemy import Column, String, DateTime, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import date
import uuid

from app.db.database import Base

class Mood(Base):
    __tablename__ = "moods"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("user.user_id"), nullable=False, index=True)
    mood = Column(String, nullable=False)
    note = Column(String, nullable=True)
    mood_date = Column(Date, nullable=False)

    user = relationship("User", back_populates="mood")
