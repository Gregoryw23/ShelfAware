#Code 2
from typing import Optional
from sqlalchemy.orm import Session
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate

class BookService:
    def __init__(self, db: Session):
        self.db = db

    def get_books(self, limit: Optional[int] = None):
        query = self.db.query(Book)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def get_book(self, book_id: str):
        return self.db.query(Book).filter(Book.book_id == book_id).first()

    def add_book(self, book_data: BookCreate):
        new_book = Book(**book_data.model_dump())
        self.db.add(new_book)
        self.db.commit()
        self.db.refresh(new_book)
        return new_book

    def update_book(self, book_id: str, updated_data: BookUpdate):
        book = self.get_book(book_id)
        if not book:
            return None

        for key, value in updated_data.model_dump(exclude_unset=True).items():
            setattr(book, key, value)

        self.db.commit()
        self.db.refresh(book)
        return book

    def delete_book(self, book_id: str):
        book = self.get_book(book_id)
        if not book:
            return False
        self.db.delete(book)
        self.db.commit()
        return True


#Code 1
'''
from sqlalchemy.orm import Session
from app.models.book import Book, BookCreate, BookUpdate

class BookService:
    def __init__(self, db: Session):
        self.db = db

    def get_books(self):
        """Retrieve all books."""
        return self.db.query(Book).all()

    def get_book(self, book_id: int):
        """Retrieve a book by ID."""
        return self.db.query(Book).filter(Book.id == book_id).first()

    def add_book(self, book_data: BookCreate):
        new_book = Book(**book_data.model_dump())
        self.db.add(new_book)
        self.db.commit()
        self.db.refresh(new_book)
        return new_book

    def update_book(self, book_id: str, updated_data: BookUpdate):
        book = self.get_book(book_id)
        if not book:
            return None

        for key, value in updated_data.model_dump(exclude_unset=True).items():
            setattr(book, key, value)

        self.db.commit()
        self.db.refresh(book)
        return book

    def delete_book(self, book_id: int):
        """Delete a book by ID."""
        book = self.get_book(book_id)
        if not book:
            return False
        self.db.delete(book)
        self.db.commit()
        return True

'''