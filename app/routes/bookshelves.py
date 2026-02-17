from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user   # or your existing current user dependency
#from app.models.bookshelf import Bookshelf
#from app.schemas.bookshelf import BookshelfCreate, BookshelfUpdate, BookshelfRead

router = APIRouter()

#@router.get("/", response_model=list[BookshelfRead])
#def list_my_bookshelf(
#    db: Session = Depends(get_db),
#    user=Depends(get_current_user),
#):
#    return db.query(Bookshelf).filter(Bookshelf.user_id == user["sub"]).all()

#@router.post("/", response_model=BookshelfRead, status_code=status.HTTP_201_CREATED)
#def add_to_bookshelf(
#    payload: BookshelfCreate,
#    db: Session = Depends(get_db),
#    user=Depends(get_current_user),
#):
#    existing = (
#        db.query(Bookshelf)
#        .filter(Bookshelf.user_id == user["sub"], Bookshelf.book_id == payload.book_id)
#        .first()
#    )
#    if existing:
#        raise HTTPException(status_code=400, detail="Book already in bookshelf")

#    item = Bookshelf(
#        user_id=user["sub"],
#        book_id=payload.book_id,
#        shelf_status=payload.shelf_status,
#    )
#    db.add(item)
#    db.commit()
#    db.refresh(item)
#    return item

#@router.put("/{book_id}", response_model=BookshelfRead)
#def update_bookshelf_item(
#    book_id: str,
#    payload: BookshelfUpdate,
#    db: Session = Depends(get_db),
#    user=Depends(get_current_user),
#):
#    item = (
#        db.query(Bookshelf)
#        .filter(Bookshelf.user_id == user["sub"], Bookshelf.book_id == book_id)
#        .first()
#    )
#    if not item:
#        raise HTTPException(status_code=404, detail="Bookshelf item not found")

#    if payload.shelf_status is not None:
#        item.shelf_status = payload.shelf_status
#    if payload.date_started is not None:
#        item.date_started = payload.date_started
#    if payload.date_finished is not None:
#        item.date_finished = payload.date_finished

#    db.commit()
#    db.refresh(item)
#    return item

#@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
#def remove_from_bookshelf(
#    book_id: str,
#    db: Session = Depends(get_db),
#    user=Depends(get_current_user),
#):
#    item = (
#        db.query(Bookshelf)
#        .filter(Bookshelf.user_id == user["sub"], Bookshelf.book_id == book_id)
#        .first()
#    )
#    if not item:
#        raise HTTPException(status_code=404, detail="Bookshelf item not found")

#    db.delete(item)
#    db.commit()
#   return