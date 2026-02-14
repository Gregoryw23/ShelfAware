from sqlalchemy import Column, String, DateTime, text, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.database import Base

def new_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "user"

    user_id = Column(String, primary_key=True, default=new_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    
    status = Column(String, nullable=False, server_default=text("'active'"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    display_name = Column(String, nullable=True)  
    bio = Column(String, nullable=True)           
    profile_photo_url = Column(String, nullable=True) 
    location = Column(String, nullable=True)     
    
    favorite_genres_json = Column(String, nullable=True) 

    # Relationship with Bookshelf
    bookshelf = relationship("Bookshelf", back_populates="user")

    # Relationship with Mood    
    mood = relationship("Mood", back_populates="user")

    # Relationship with password_reset    
    password_resets = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    