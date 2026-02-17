"""
Script to load books from CSV into SQLite database
Usage: python -m scripts.load_books_data
"""
import os
import sys
import csv
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, DATABASE_URL
from app.models.book import Book
from app.models.genre import Genre
from app.models.book_genre import BookGenre


def load_books_from_csv(csv_path: str):
    """Load books and genres from CSV file into database"""

    # Create database engine and session
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(bind=engine)  # Ensure all tables exist
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print(f"Loading books from {csv_path}...")

        with open(csv_path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            books_count = 0
            genres_cache = {}  # Cache genre names to IDs to avoid duplicates

            for row in reader:
                try:
                    # Skip rows with missing book_id
                    if not row.get("book_id") or not row.get("title"):
                        print(
                            f"Skipping incomplete row: {row.get('title', 'Unknown')}"
                        )
                        continue
                    # Parse published_date
                    published_date = None
                    if row.get("published_date"):
                        try:
                            published_date = datetime.strptime(
                                row["published_date"], "%B %d, %Y"
                            ).date()
                        except ValueError:
                            try:
                                published_date = datetime.strptime(
                                    row["published_date"], "%Y-%m-%d"
                                ).date()
                            except ValueError:
                                print(
                                    f"Warning: Could not parse date '{row['published_date']}' for book {row.get('title')}"
                                )
                                published_date = None

                    # Check if book already exists
                    existing_book = session.query(Book).filter_by(
                        book_id=row["book_id"]
                    ).first()
                    if existing_book:
                        print(f"Book {row['book_id']} already exists, skipping...")
                        continue

                    # Create Book object
                    book = Book(
                        book_id=row["book_id"],
                        title=row["title"],
                        subtitle=row.get("subtitle") or None,
                        cover_image_url=row.get("cover_image_url") or None,
                        abstract=row.get("abstract") or None,
                        CommunitySynopsis=row.get("CommunityReview") or None,
                        page_count=int(row["page_count"])
                        if row.get("page_count")
                        else None,
                        published_date=published_date,
                    )

                    session.add(book)
                    session.flush()  # Flush to ensure book_id is available

                    # Handle genres
                    genre_names = row.get("Genre")
                    if genre_names:
                        # Split genres by comma
                        for genre_name in genre_names.split("/"):
                            genre_name = genre_name.strip()
                            if genre_name:
                                # Check if genre already exists in cache or DB
                                if genre_name not in genres_cache:
                                    existing_genre = session.query(Genre).filter_by(
                                        name=genre_name
                                    ).first()
                                    if existing_genre:
                                        genres_cache[genre_name] = existing_genre.genre_id
                                    else:
                                        genre = Genre(name=genre_name)
                                        session.add(genre)
                                        session.flush()
                                        genres_cache[genre_name] = genre.genre_id

                                # Link genre to book
                                genre_id = genres_cache[genre_name]
                                bg = BookGenre(
                                    book_id=book.book_id, genre_id=genre_id
                                )
                                session.add(bg)

                    books_count += 1
                    if books_count % 10 == 0:
                        print(f"Processed {books_count} books...")

                except Exception as e:
                    print(f"Error processing row: {row.get('title', 'Unknown')} - {e}")
                    session.rollback()
                    continue

        # Commit all changes
        session.commit()
        print(f"\nSuccessfully loaded {books_count} books into database!")

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading books: {e}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    # Use default path relative to project root
    csv_file = Path(__file__).parent.parent / "BooksDB_wGenres.csv"

    if not csv_file.exists():
        print(f"CSV file not found at {csv_file}")
        print("Please ensure BooksDB_wGenres.csv is in the project root directory.")
        sys.exit(1)

    load_books_from_csv(str(csv_file))
