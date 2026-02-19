from sqlalchemy import Column, String, DateTime, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import date
import uuid

from app.db.database import Base

class Mood(Base):
    __tablename__ = "moods"

    id = Column(Integer, primary_key=True)

    # Use UUID type for user_id to match the User model if user_id is a UUID
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False)  # Correct reference

    mood = Column(String, nullable=False)
    note = Column(String, nullable=True)
    mood_date = Column(Date, nullable=False)

    # Relationship to User model
    user = relationship("User", back_populates="moods")  # Ensure 'User' has back_populates set
