#!/usr/bin/env python3
"""
Import Goodreads reviews from CSV into ShelfAware database.

IMPORTANT: Web scraping Goodreads violates their Terms of Service.
This script imports from CSV files instead (safe & recommended).

How to export reviews from Goodreads:
1. Visit: https://www.goodreads.com/review/import_export
2. Download your review shelf as CSV (contains all your reviews + ratings)
3. Use this script to import into ShelfAware

CSV Format Expected:
  book_id,title,author,rating,review_text,date_read
  (or minimal: book_id,rating,review_text)
"""

import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import SessionLocal
from app.models.review import Review
from app.models.book import Book
from app.models.user import User
from app.models.mood import Mood


def import_reviews_from_csv(csv_file: str, user_id: str) -> dict:
    """
    Import reviews from CSV file into database.
    
    Args:
        csv_file: Path to CSV file
        user_id: ID of user to associate reviews with
    
    Returns:
        Dict with import stats (success_count, error_count, errors)
    """
    db = SessionLocal()
    stats = {
        "success_count": 0,
        "error_count": 0,
        "skipped_count": 0,
        "errors": []
    }
    
    try:
        # Verify user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            print(f"❌ User '{user_id}' not found in database")
            return stats
        
        print(f"✓ Found user: {user_id}")
        
        # Open and parse CSV
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames:
                print("❌ CSV file is empty")
                return stats
            
            print(f"✓ CSV columns: {reader.fieldnames}")
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Extract fields (support multiple column name variations)
                    book_id = row.get("book_id") or row.get("id") or row.get("bookid")
                    rating = row.get("rating") or row.get("my_rating")
                    review_text = row.get("review_text") or row.get("review") or row.get("my_review")
                    
                    if not book_id or not rating:
                        stats["skipped_count"] += 1
                        continue
                    
                    # Convert rating to int
                    try:
                        rating = int(float(rating))
                    except (ValueError, TypeError):
                        stats["errors"].append(f"Row {row_num}: Invalid rating '{rating}'")
                        stats["error_count"] += 1
                        continue
                    
                    # Validate rating range
                    if not (1 <= rating <= 5):
                        stats["errors"].append(f"Row {row_num}: Rating '{rating}' not in range 1-5")
                        stats["error_count"] += 1
                        continue
                    
                    # Check if book exists
                    book = db.query(Book).filter(Book.book_id == str(book_id)).first()
                    if not book:
                        stats["errors"].append(f"Row {row_num}: Book ID '{book_id}' not found")
                        stats["error_count"] += 1
                        continue
                    
                    # Check for duplicate review (user + book)
                    existing = db.query(Review).filter(
                        Review.user_id == user_id,
                        Review.book_id == str(book_id)
                    ).first()
                    if existing:
                        stats["skipped_count"] += 1
                        continue
                    
                    # Create review
                    review = Review(
                        book_id=str(book_id),
                        user_id=user_id,
                        rating=rating,
                        body=review_text or ""
                    )
                    db.add(review)
                    db.flush()
                    
                    # Add mood entry if review text is present
                    if review_text and review_text.strip():
                        mood_entry = Mood(
                            user_id=user_id,
                            mood="imported",
                            mood_date=datetime.utcnow().date()
                        )
                        db.add(mood_entry)
                    
                    stats["success_count"] += 1
                    
                except Exception as e:
                    stats["errors"].append(f"Row {row_num}: {str(e)}")
                    stats["error_count"] += 1
                    db.rollback()
        
        # Commit successful reviews
        db.commit()
        print(f"\n✓ Successfully imported {stats['success_count']} reviews")
        if stats["skipped_count"] > 0:
            print(f"⊘ Skipped {stats['skipped_count']} duplicate/incomplete reviews")
        if stats["error_count"] > 0:
            print(f"❌ {stats['error_count']} errors encountered")
            for error in stats["errors"][:10]:
                print(f"   {error}")
            if len(stats["errors"]) > 10:
                print(f"   ... and {len(stats['errors']) - 10} more errors")
        
        return stats
    
    except FileNotFoundError:
        print(f"❌ File not found: {csv_file}")
        return stats
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return stats
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Import Goodreads reviews from CSV into ShelfAware"
    )
    parser.add_argument(
        "--csv",
        required=True,
        help="Path to CSV file with reviews"
    )
    parser.add_argument(
        "--user",
        required=True,
        help="User ID to associate reviews with"
    )
    
    args = parser.parse_args()
    
    print(f"Importing reviews from: {args.csv}")
    print(f"User ID: {args.user}\n")
    stats = import_reviews_from_csv(args.csv, args.user)
    
    print("\n" + "="*80)
    print("IMPORT SUMMARY")
    print("="*80)
    print(f"Success:  {stats['success_count']} reviews imported")
    print(f"Skipped:  {stats['skipped_count']} duplicates/incomplete")
    print(f"Errors:   {stats['error_count']} failed")
    print("="*80)
