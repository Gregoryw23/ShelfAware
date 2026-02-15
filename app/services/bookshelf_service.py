from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, asc, or_

from app.models.bookshelf import Bookshelf
from app.models.book import Book  # Optional existence check (can remove if not needed)


STATUS_ORDER = {
    "want_to_read": 0,
    "currently_reading": 1,
    "read": 2,
}

SORT_MAP = {
    "date_added": Bookshelf.date_added,
    "updated_at": Bookshelf.updated_at,
    "date_finished": Bookshelf.date_finished,
}


def _now() -> datetime:
    # naive UTC for consistency with your auth reset token style
    return datetime.utcnow()


def _validate_transition(old: str, new: str) -> None:
    if new not in STATUS_ORDER:
        raise ValueError("Invalid shelf_status")
    if STATUS_ORDER[new] < STATUS_ORDER.get(old, 0):
        raise ValueError("Cannot move status backwards")


def add_to_shelf(db: Session, *, user_id: str, book_id: str) -> Bookshelf:
    # Optional: verify book exists (recommended)
    exists = db.execute(select(Book.book_id).where(Book.book_id == book_id)).scalar_one_or_none()
    if not exists:
        raise ValueError("Book not found")

    existing = db.execute(
        select(Bookshelf).where(
            Bookshelf.user_id == user_id,
            Bookshelf.book_id == book_id,
        )
    ).scalar_one_or_none()

    if existing:
        # Mark as duplicate so route can map to 409
        raise ValueError("DUPLICATE")

    now = _now()
    item = Bookshelf(
        user_id=user_id,
        book_id=book_id,
        shelf_status="want_to_read",
        date_added=now,
        updated_at=now,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_shelf(db: Session, *, user_id: str, book_id: str) -> None:
    item = db.execute(
        select(Bookshelf).where(
            Bookshelf.user_id == user_id,
            Bookshelf.book_id == book_id,
        )
    ).scalar_one_or_none()

    if not item:
        raise ValueError("NOT_FOUND")

    db.delete(item)
    db.commit()


def update_status(db: Session, *, user_id: str, book_id: str, new_status: str) -> Bookshelf:
    item = db.execute(
        select(Bookshelf).where(
            Bookshelf.user_id == user_id,
            Bookshelf.book_id == book_id,
        )
    ).scalar_one_or_none()

    if not item:
        raise ValueError("NOT_FOUND")

    old_status = item.shelf_status
    _validate_transition(old_status, new_status)

    now = _now()
    item.shelf_status = new_status
    item.updated_at = now

    if new_status == "currently_reading":
        if item.date_started is None:
            item.date_started = now

    if new_status == "read":
        if item.date_started is None:
            item.date_started = now
        if item.date_finished is None:
            item.date_finished = now
        if item.date_finished < item.date_started:
            raise ValueError("Invalid dates: finished before started")

    db.commit()
    db.refresh(item)
    return item


def list_shelf(
    db: Session,
    *,
    user_id: str,
    status: Optional[str] = None,
    sort: str = "updated_at",
    order: str = "desc",
) -> List[Bookshelf]:
    q = select(Bookshelf).where(Bookshelf.user_id == user_id)

    if status:
        q = q.where(Bookshelf.shelf_status == status)

    sort_col = SORT_MAP.get(sort, Bookshelf.updated_at)
    q = q.order_by(desc(sort_col) if order == "desc" else asc(sort_col))

    return db.execute(q).scalars().all()


def get_timeline(db: Session, *, user_id: str) -> List[Bookshelf]:
    q = (
        select(Bookshelf)
        .where(Bookshelf.user_id == user_id)
        .where(or_(Bookshelf.date_started.isnot(None), Bookshelf.date_finished.isnot(None)))
        .order_by(desc(Bookshelf.date_finished), desc(Bookshelf.date_started), desc(Bookshelf.updated_at))
    )
    return db.execute(q).scalars().all()


def get_stats(db: Session, *, user_id: str) -> Dict[str, Any]:
    items = db.execute(
        select(Bookshelf)
        .where(Bookshelf.user_id == user_id)
        .where(Bookshelf.shelf_status == "read")
        .where(Bookshelf.date_finished.isnot(None))
    ).scalars().all()

    now = _now()
    this_year = now.year
    this_month = (now.year, now.month)

    read_year = 0
    read_month = 0

    durations_days: List[float] = []
    finished_dates = []

    for it in items:
        df = it.date_finished
        if df is None:
            continue

        if df.year == this_year:
            read_year += 1
        if (df.year, df.month) == this_month:
            read_month += 1

        start = it.date_started or it.date_added
        if start and df >= start:
            durations_days.append((df - start).total_seconds() / 86400.0)

        finished_dates.append(df.date())

    avg_days = (sum(durations_days) / len(durations_days)) if durations_days else None

    unique_days = sorted(set(finished_dates))
    best = 0
    streak = 0
    prev = None
    for d in unique_days:
        if prev is None:
            streak = 1
        else:
            streak = streak + 1 if (d - prev).days == 1 else 1
        best = max(best, streak)
        prev = d

    current = 0
    if unique_days:
        last = unique_days[-1]
        gap = (now.date() - last).days
        if gap in (0, 1):
            current = 1
            for i in range(len(unique_days) - 2, -1, -1):
                if (unique_days[i + 1] - unique_days[i]).days == 1:
                    current += 1
                else:
                    break

    return {
        "read_this_month": read_month,
        "read_this_year": read_year,
        "avg_days_to_finish": avg_days,
        "current_streak_days": current,
        "best_streak_days": best,
    }