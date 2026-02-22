from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class UserProfile(Base):
    __tablename__ = "user_profile"

    # Reference 'user.user_id' (singular) to match your User model
    user_id = Column(String, ForeignKey("user.user_id"), primary_key=True)
    display_name = Column(String, nullable=False)
    profile_photo_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    location = Column(String, nullable=True)
    favorite_genres_json = Column(String, nullable=True)

    # Establish bidirectional relationship with User model
    user = relationship("User", back_populates="profile", uselist=False)