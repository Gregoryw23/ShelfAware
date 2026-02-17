from pydantic import BaseModel
from typing import Optional

class ChromaBookInfo(BaseModel):
    id: str # Corresponds to ShelfAware's Book.book_id (UUID string)
    title: str
    abstract: Optional[str] = None # Corresponds to ShelfAware's Book.abstract
