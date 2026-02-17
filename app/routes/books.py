from fastapi import APIRouter, HTTPException, Depends, status
from app.models.book import Book
from app.schemas.book import BookInfo, BookResponse
from app.services.book_service import BookService
from app.dependencies.services import get_book_service

router = APIRouter()

@router.get("/", response_model=list[BookResponse])
def get_books(service: BookService = Depends(get_book_service)):
    return service.get_books()

@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, service: BookService = Depends(get_book_service)):
    book = service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def add_book(book: BookInfo, service: BookService = Depends(get_book_service)):
    return service.add_book(book)

@router.put("/{book_id}", response_model=BookResponse)
def update_book(book_id: int, updated_book: BookInfo, service: BookService = Depends(get_book_service)):
    book = service.update_book(book_id, updated_book)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.delete("/{book_id}")
def delete_book(book_id: int, service: BookService = Depends(get_book_service)):
    success = service.delete_book(book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}
