from sqlalchemy import Column, String, DateTime, Text, text
from sqlalchemy.orm import relationship

from datetime import datetime
import uuid

from app.db.database import Base

def new_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "user"

    user_id = Column(String, primary_key=True, default=new_uuid)

    cognito_sub = Column(String, unique=True, nullable=False, index=True)

    email = Column(String, unique=True, nullable=False, index=True)
    
    status = Column(String, nullable=False, server_default=text("'active'"))
    created_at = Column(DateTime, nullable=False, default=datetime)
    last_login = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # Relationship with UserProfile
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", single_parent=True)
    
    # Relationship with Bookshelf
    bookshelf = relationship("Bookshelf", back_populates="user")

    # Relationship with Mood    
    mood = relationship("Mood", back_populates="user")

    # Relationship with Review
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")

    # One-to-one relationship with UserProfile
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    