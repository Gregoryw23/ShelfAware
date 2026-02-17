#Code 2
# app/models/user_profile.py
from sqlalchemy import Column, String, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.database import Base


def new_uuid():
    return str(uuid.uuid4())


class UserProfile(Base):
    __tablename__ = "user_profile"

    profile_id = Column(String, primary_key=True, default=new_uuid)

    # One-to-one link to User
    user_id = Column(String, ForeignKey("user.user_id"), unique=True, nullable=False, index=True)

    display_name = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    profile_photo_url = Column(String, nullable=True)
    location = Column(String, nullable=True)
    favorite_genres_json = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow,
    )

    # Relationship back to User
    user = relationship("User", back_populates="profile")

#Code 1
'''
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class UserProfile(Base):
    __tablename__ = "user_profile"

    # user_id is both the primary key (primary_key=True) and a foreign key (ForeignKey)
    # This establishes a 1-to-1 relationship with the User table
    user_id = Column(String, ForeignKey("user.user_id"), primary_key=True)

    # Corresponds to "varchar NN" (Not Null) in the ER diagram
    display_name = Column(String, nullable=False)

    # Other fields are optional (nullable=True)
    profile_photo_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    location = Column(String, nullable=True)
    favorite_genres_json = Column(String, nullable=True)

    # Define relationship
    # Note: For this to work fully, a relationship should ideally be added to app/models/user.py as well.
    # However, even if user.py is not modified, this line allows access to the User via profile.user.
    # If you cannot modify user.py, consider removing back_populates to avoid mapping errors.
    user = relationship("User", back_populates="profile")
    '''