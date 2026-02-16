'''
#For non hardcoded user_id in bookshelf routes, import get_current_user dependency

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
#from app.dependencies.auth import get_current_user
#from app.dependencies.dev_auth import get_current_user_dev as get_current_user

from app.schemas.bookshelf import BookshelfCreate, BookshelfStatusUpdate, BookshelfOut
from app.services import bookshelf_service

#TEST_USER_ID = "52a343c8-e3f3-4ed1-a145-17c09987657c"


router = APIRouter(prefix="/bookshelf", tags=["Bookshelf"])


@router.post("", response_model=BookshelfOut, status_code=status.HTTP_201_CREATED)
def add_book(payload: BookshelfCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        return bookshelf_service.add_to_shelf(db, user_id=user.user_id, book_id=payload.book_id)
    except ValueError as e:
        msg = str(e)
        if msg == "DUPLICATE":
            raise HTTPException(status_code=409, detail="Book already exists in your shelf")
        if msg == "Book not found":
            raise HTTPException(status_code=404, detail="Book not found")
        raise HTTPException(status_code=400, detail=msg)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_book(book_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        bookshelf_service.remove_from_shelf(db, user_id=user.user_id, book_id=book_id)
    except ValueError as e:
        if str(e) == "NOT_FOUND":
            raise HTTPException(status_code=404, detail="Book not found in your shelf")
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{book_id}/status", response_model=BookshelfOut)
def change_status(
    book_id: str,
    payload: BookshelfStatusUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        return bookshelf_service.update_status(
            db,
            user_id=user.user_id,
            book_id=book_id,
            new_status=payload.shelf_status,
        )
    except ValueError as e:
        msg = str(e)
        if msg == "NOT_FOUND":
            raise HTTPException(status_code=404, detail="Book not found in your shelf")
        raise HTTPException(status_code=400, detail=msg)


@router.get("", response_model=list[BookshelfOut])
def list_shelf(
    status_filter: str | None = Query(default=None, alias="status", pattern="^(want_to_read|currently_reading|read)$"),
    sort: str = Query(default="updated_at", pattern="^(date_added|updated_at|date_finished)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return bookshelf_service.list_shelf(
        db,
        user_id=user.user_id,
        status=status_filter,
        sort=sort,
        order=order,
    )


@router.get("/timeline", response_model=list[BookshelfOut])
def timeline(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return bookshelf_service.get_timeline(db, user_id=user.user_id)


@router.get("/stats")
def stats(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return bookshelf_service.get_stats(db, user_id=user.user_id)

'''

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.bookshelf import BookshelfCreate, BookshelfStatusUpdate, BookshelfOut
from app.services import bookshelf_service

# ✅ Hardcoded test user id (must exist in DB)
TEST_USER_ID = "52a343c8-e3f3-4ed1-a145-17c09987657c"

router = APIRouter(prefix="/bookshelf", tags=["Bookshelf"])


@router.post("", response_model=BookshelfOut, status_code=status.HTTP_201_CREATED)
def add_book(payload: BookshelfCreate, db: Session = Depends(get_db)):
    try:
        return bookshelf_service.add_to_shelf(
            db,
            user_id=TEST_USER_ID,
            book_id=payload.book_id
        )
    except ValueError as e:
        msg = str(e)
        if msg == "DUPLICATE":
            raise HTTPException(status_code=409, detail="Book already exists in your shelf")
        if msg == "Book not found":
            raise HTTPException(status_code=404, detail="Book not found")
        raise HTTPException(status_code=400, detail=msg)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_book(book_id: str, db: Session = Depends(get_db)):
    try:
        bookshelf_service.remove_from_shelf(
            db,
            user_id=TEST_USER_ID,
            book_id=book_id
        )
    except ValueError as e:
        if str(e) == "NOT_FOUND":
            raise HTTPException(status_code=404, detail="Book not found in your shelf")
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{book_id}/status", response_model=BookshelfOut)
def change_status(
    book_id: str,
    payload: BookshelfStatusUpdate,
    db: Session = Depends(get_db),
):
    try:
        return bookshelf_service.update_status(
            db,
            user_id=TEST_USER_ID,
            book_id=book_id,
            new_status=payload.shelf_status,
        )
    except ValueError as e:
        msg = str(e)
        if msg == "NOT_FOUND":
            raise HTTPException(status_code=404, detail="Book not found in your shelf")
        raise HTTPException(status_code=400, detail=msg)


@router.get("", response_model=list[BookshelfOut])
def list_shelf(
    status_filter: str | None = Query(default=None, alias="status", pattern="^(want_to_read|currently_reading|read)$"),
    sort: str = Query(default="updated_at", pattern="^(date_added|updated_at|date_finished)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    return bookshelf_service.list_shelf(
        db,
        user_id=TEST_USER_ID,
        status=status_filter,
        sort=sort,
        order=order,
    )


@router.get("/timeline", response_model=list[BookshelfOut])
def timeline(db: Session = Depends(get_db)):
    return bookshelf_service.get_timeline(db, user_id=TEST_USER_ID)


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return bookshelf_service.get_stats(db, user_id=TEST_USER_ID)
