from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from datetime import datetime
import uuid

from app.db.db import Base

def new_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "user"
    user_id = Column(String, primary_key=True, default=new_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    status = Column(String, nullable=False, server_default=text("'active'"))
    created_at = Column(DateTime, nullable=False, default=datetime)
    last_login = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)