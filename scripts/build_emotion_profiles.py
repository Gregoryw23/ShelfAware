#!/usr/bin/env python3
"""
Build/rebuild emotion profiles for books based on reviews.

This script:
1. Fetches all reviews for each book
2. Extracts emotions from review text
3. Creates emotion profiles (for recommendations)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.book import Book
from app.models.review import Review
from app.services.mood_recommendation.emotion_extractor import (
    EmotionExtractor,
    emotion_lexicon
)
import json

def build_emotion_profiles(limit: int = None) -> dict:
    """
    Build emotion profiles for all books in database.
    
    Args:
        limit: Optional limit on number of books to process (for testing)
    
    Returns:
        Dict with stats (books_processed, reviews_analyzed, errors)
    """
    db = SessionLocal()
    # Ensure DB has emotion_profile column; add if missing (simple migration)
    try:
        # SQLite: add column if it doesn't exist
        db.execute("ALTER TABLE book ADD COLUMN emotion_profile TEXT")
        db.commit()
    except Exception:
        # Ignore if column already exists or migration not needed
        db.rollback()
    stats = {
        "books_processed": 0,
        "reviews_analyzed": 0,
        "books_without_reviews": 0,
        "emotion_profiles_created": 0,
        "errors": []
    }
    
    try:
        # Initialize emotion extractor
        emotion_extractor = EmotionExtractor(emotion_lexicon)
        print(f"✓ Initialized emotion extractor with {len(emotion_lexicon)} emotions")
        
        # Get all books
        books_query = db.query(Book)
        if limit:
            books_query = books_query.limit(limit)
        books = books_query.all()
        
        print(f"Processing {len(books)} books...\n")
        
        for idx, book in enumerate(books, start=1):
            try:
                # Get all reviews for this book
                reviews = db.query(Review).filter(
                    Review.book_id == book.book_id
                ).all()
                
                # Initialize empty profile for all books
                emotions_aggregated = {
                    emotion: {"count": 0, "score": 0.0} 
                    for emotion in emotion_lexicon.keys()
                }
                
                if not reviews:
                    stats["books_without_reviews"] += 1
                    print(f"[{idx}/{len(books)}] {book.title}: No reviews → default empty profile")
                else:
                    # Extract emotions from all reviews
                    for review in reviews:
                        if review.body:
                            print(f"    Review: {review.body}")
                            try:
                                emotions = emotion_extractor.extract_emotions(review.body)
                            except Exception as e:
                                print(f"    ❌ Emotion extraction failed for review: {str(e)}")
                                stats["errors"].append(f"Review extraction failed for book {book.title}: {str(e)}")
                                continue

                            print(f"    Extracted: {emotions}")
                            counts = emotions.get("counts", {}) or {}
                            scores = emotions.get("scores", {}) or {}
                            if not counts and not scores:
                                print("    ⚠️ No emotions detected in this review")

                            for emotion, count in counts.items():
                                emotions_aggregated[emotion]["count"] += count
                                emotions_aggregated[emotion]["score"] += scores.get(emotion, 0.0)
                            stats["reviews_analyzed"] += 1
                    
                    # Print top emotions for book
                    top_emotions = sorted(
                        [(e, d["score"]) for e, d in emotions_aggregated.items()],
                        key=lambda x: x[1],
                        reverse=True
                    )[:3]
                    top_emotions_str = ", ".join(
                        [f"{e}({s:.1f})" for e, s in top_emotions if s > 0]
                    ) or "No emotions detected"
                    
                    print(f"[{idx}/{len(books)}] {book.title}: {len(reviews)} reviews analyzed")
                    print(f"             Top emotions: {top_emotions_str}\n")
                
                # Aggregate and store in book model (emotion_profile column) — always save!
                if hasattr(book, "emotion_profile"):
                    try:
                        profile_json = json.dumps(emotions_aggregated)
                        book.emotion_profile = profile_json
                        db.add(book)
                        db.commit()
                        if reviews:
                            print(f"    ✅ Saved emotion profile for '{book.title}' to DB")
                        stats["emotion_profiles_created"] += 1
                    except Exception as e:
                        db.rollback()
                        stats["errors"].append(f"Failed to save profile for {book.title}: {str(e)}")
                        print(f"    ❌ Failed to save profile: {str(e)}")
                
                stats["books_processed"] += 1
                
            except Exception as e:
                stats["errors"].append(f"Book {book.title}: {str(e)}")
                print(f"[{idx}/{len(books)}] ❌ Error processing {book.title}: {str(e)}\n")
        
        # Commit all changes
        db.commit()
        
        # Print summary
        print("\n" + "="*80)
        print("EMOTION PROFILE BUILD SUMMARY")
        print("="*80)
        print(f"Books processed:          {stats['books_processed']}")
        print(f"Reviews analyzed:         {stats['reviews_analyzed']}")
        print(f"Books without reviews:    {stats['books_without_reviews']}")
        print(f"Emotion profiles created: {stats['emotion_profiles_created']}")
        if stats["errors"]:
            print(f"Errors:                   {len(stats['errors'])}")
            for error in stats["errors"][:5]:
                print(f"  - {error}")
            if len(stats["errors"]) > 5:
                print(f"  ... and {len(stats['errors']) - 5} more")
        print("="*80)
        
        return stats
    
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        return stats
    finally:
        db.close()


def show_emotion_profile_stats():
    """Show emotion extraction capabilities."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        EMOTION PROFILE SYSTEM                              ║
╚════════════════════════════════════════════════════════════════════════════╝

This system extracts 8 emotions from review text:

  happy       : joy, love, wonderful, amazing, brilliant
  sad         : sad, depressed, disappointing, boring, waste
  angry       : angry, infuriating, frustrated, hate, terrible
  excited     : excited, thrilled, thrilling, suspenseful, gripping
  scared      : scared, horror, creepy, haunted, terrifying
  romantic    : romantic, love, tenderness, touching, emotional
  suspenseful : suspenseful, mystery, twists, page turner, thriller
  dark        : dark, grim, evil, death, tragic

The emotion profiles are used by the recommendation engine to:
  - Find books similar in emotional tone (content-based)
  - Find users with similar emotional preferences (collaborative)
  - Recommend books matching user's current mood (future feature)

═══════════════════════════════════════════════════════════════════════════════
    """)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build emotion profiles for books from reviews"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of books to process (for testing)"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show emotion categories and exit"
    )
    
    args = parser.parse_args()
    
    if args.info:
        show_emotion_profile_stats()
    else:
        print("Building emotion profiles from reviews...\n")
        stats = build_emotion_profiles(limit=args.limit)
