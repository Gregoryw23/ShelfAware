'''
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

class Bookshelf(Base):
    __tablename__ = "bookshelf"

    user_id = Column(String, primary_key=True)
    book_id = Column(String, ForeignKey("book.book_id"), primary_key=True)

    shelf_status = Column(String, nullable=False, default="want_to_read")
    date_added = Column(DateTime, default=datetime.utcnow)
    date_started = Column(DateTime, nullable=True)
    date_finished = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("Book", back_populates="bookshelves")
    '''

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base

class Bookshelf(Base):
    __tablename__ = "bookshelf"

    user_id = Column(String, primary_key=True)  # stub for now (no FK yet)
    book_id = Column(String, ForeignKey("book.book_id"), primary_key=True)

    shelf_status = Column(String, nullable=False, default="want_to_read")
    date_added = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_started = Column(DateTime, nullable=True)
    date_finished = Column(DateTime, nullable=True)

    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    book = relationship("Book", back_populates="bookshelves")

