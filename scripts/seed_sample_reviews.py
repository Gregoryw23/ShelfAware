#!/usr/bin/env python3
"""
Seed sample reviews into the database for testing recommendations.

These sample reviews are realistic for history/biography books with varied
emotional content to test the emotion extraction and recommendation engine.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import SessionLocal
from app.models.review import Review
from app.models.book import Book
from app.models.user import User


# Sample reviews for biography/history books with varied emotions
SAMPLE_REVIEWS = {
    "6462": [  # George Washington biography
        {
            "rating": 5,
            "body": "Absolutely brilliant! This biography captures Washington's incredible leadership and determination. A masterpiece of historical writing that is both engaging and deeply insightful. I was thrilled to learn about his strategic genius."
        },
        {
            "rating": 4,
            "body": "Excellent account of Washington's life. The author provides wonderful details about his character and challenges. Some sections are a bit dense, but overall it's a compelling and well-researched work."
        },
        {
            "rating": 5,
            "body": "Amazing! This book perfectly demonstrates why Washington is considered great. The narrative is gripping and the historical accuracy is impressive. I felt inspired by his dedication to duty."
        },
        {
            "rating": 3,
            "body": "Good historical information, though the pacing is slow in parts. The biography does a solid job covering his military campaigns and presidency. Worth reading if you're interested in American history."
        },
        {
            "rating": 4,
            "body": "Wonderful examination of Washington as both a military and political leader. The author's research is evident and the writing is mostly engaging. A few chapters dragged a bit, but the overall picture is compelling."
        },
        {
            "rating": 5,
            "body": "Brilliant! The author captures Washington's complexity beautifully. This is one of the finest biographies I've read. Absolutely riveting from start to finish. I was thrilled and enlightened throughout."
        },
        {
            "rating": 4,
            "body": "Very good biography with excellent attention to detail. Shows Washington's struggles and triumphs in a balanced way. The writing is clear and the story is engaging. Highly recommended for history lovers."
        },
    ],
    "93996": [  # Hitler biography
        {
            "rating": 5,
            "body": "Comprehensive and deeply researched. This biography provides crucial historical insights into a dark period. The author's meticulous documentation is impressive, though the subject matter is disturbing and tragic."
        },
        {
            "rating": 5,
            "body": "Extraordinary historical work. The detailed analysis is unfortunately necessary to understand how such evil could emerge. Sobering and important reading. The writer's commitment to accuracy is remarkable despite the dark subject."
        },
        {
            "rating": 4,
            "body": "Well-written and thoroughly researched biography. It's a difficult read given the tragic historical events, but essential for understanding World War II. The author handles the grim subject matter with appropriate seriousness."
        },
        {
            "rating": 4,
            "body": "Powerful and important biography that illuminates how a terrible figure rose to power. The historical detail is impressive. It's a heavy and sometimes dark read, but incredibly important work."
        },
        {
            "rating": 5,
            "body": "Masterful biography of a horrifying historical figure. The research is meticulous and the narrative gripping despite the tragic subject. Essential reading for understanding this dark period of history."
        },
        {
            "rating": 3,
            "body": "Comprehensively covers Hitler's life and rise to power. The detailed accounts are both informative and deeply disturbing. A challenging but necessary read that highlights one of history's darkest chapters."
        },
    ],
    "1206073": [  # Washington's Crossing
        {
            "rating": 5,
            "body": "Absolutely thrilling account of Washington's bold crossing! The excitement builds throughout and the historical detail is fantastic. I was on the edge of my seat reading about this pivotal moment. Brilliant storytelling!"
        },
        {
            "rating": 5,
            "body": "Amazing narrative of a desperate military gamble that changed American history. The author brings the excitement and danger of the winter campaign to life. Gripping and inspiring! One of the best history books I've read."
        },
        {
            "rating": 4,
            "body": "Excellent account of this crucial moment in American history. The writing is engaging and the research is thorough. The suspenseful narrative keeps you invested in the outcome, even though you know the result."
        },
        {
            "rating": 5,
            "body": "What an exciting and well-told story! The crossing is presented with thrilling detail and the stakes feel real. Washington's courage and determination are inspiring. This book is fantastic!"
        },
        {
            "rating": 4,
            "body": "Very well researched and compellingly written. The author captures the tension and excitement of the moment brilliantly. A fantastic read for those interested in Revolutionary War history."
        },
        {
            "rating": 3,
            "body": "Solid historical account with good narrative flow. While interesting, some parts feel repetitive. The overall story is compelling and historically important, though occasionally tedious."
        },
        {
            "rating": 4,
            "body": "Gripping narrative that makes history come alive. The author's vivid descriptions of the crossing and surrounding events are wonderful. A thrilling read that's also historically accurate."
        },
    ],
    "2368": [  # Mornings on Horseback
        {
            "rating": 5,
            "body": "Beautiful and intimate biography of young Theodore Roosevelt! The author captures his joy in nature and outdoor adventures wonderfully. Inspirational portrait of a determined young man. Deeply moving and well-written."
        },
        {
            "rating": 4,
            "body": "Excellent portrait of Roosevelt's formative years. The writing is lovely and captures his passionate love of the outdoors. Well-researched and engaging. A wonderful introduction to Roosevelt's character."
        },
        {
            "rating": 5,
            "body": "Wonderful book! The author brings young TR to life with beautiful prose and rich historical detail. His early adventures on horseback are thrilling and his character development is inspiring."
        },
        {
            "rating": 4,
            "body": "Very well written biography with touching details about Roosevelt's youth. The descriptions of his horseback riding and nature experiences are vivid. Engaging and inspiring throughout."
        },
        {
            "rating": 5,
            "body": "Beautiful and moving account of Roosevelt's early life. The author's narrative is tender and insightful. I felt deeply connected to young Theodore's joys and struggles. Splendid book!"
        },
        {
            "rating": 3,
            "body": "Good biography of Theodore Roosevelt's youth, though it gets a bit slow at times. The writing about his outdoor adventures is charming. Overall solid but occasionally meandering."
        },
        {
            "rating": 4,
            "body": "Touching narrative of Roosevelt's formative years. The author captures his character beautifully through stories of horseback riding and outdoor adventures. Well-researched and emotionally resonant."
        },
    ],
    "10335318": [  # Destiny of the Republic
        {
            "rating": 5,
            "body": "Absolutely thrilling! This page-turner covers Garfield's assassination with incredible suspense. The historical narrative is gripping and the writing is exceptional. I was captivated throughout. Brilliant book!"
        },
        {
            "rating": 5,
            "body": "Extraordinary account of a pivotal and tragic moment in American history! The author weaves multiple perspectives together masterfully. Exciting, moving, and deeply important. Absolutely phenomenal!"
        },
        {
            "rating": 4,
            "body": "Gripping narrative about Garfield and his tragic death. The author builds suspense expertly and explores the impact on the nation. Well-researched and compelling. A fantastic historical read."
        },
        {
            "rating": 5,
            "body": "Amazing! This book is exciting, tragic, and deeply moving. The author's storytelling is phenomenal. I couldn't put it down. A thrilling exploration of a fascinating and tragic period."
        },
        {
            "rating": 4,
            "body": "Excellent historical narrative that brings Garfield's presidency and assassination to life. The writing is engaging and the research is thorough. Moving and important account of a dark chapter in American history."
        },
        {
            "rating": 5,
            "body": "Wonderful and thrilling biography! The author captures both the excitement and tragedy of the era brilliantly. The narrative pulls you in and keeps you engaged. Highly recommended!"
        },
        {
            "rating": 4,
            "body": "Very well-written account of Garfield's life and death. The historical context is clear and the narrative is compelling. A moving and important book that highlights a tragic moment in America's past."
        },
    ],
}


def create_test_user_if_needed(db):
    """Create a test user if one doesn't exist."""
    test_user = db.query(User).filter(User.email == "test@example.com").first()
    if test_user:
        return test_user.user_id
    
    user_id = str(uuid.uuid4())
    new_user = User(
        user_id=user_id,
        cognito_sub="test_sub_123",
        email="test@example.com",
    )
    db.add(new_user)
    db.commit()
    print(f"✓ Created test user: {user_id}")
    return user_id


def seed_reviews() -> dict:
    """
    Seed sample reviews for testing.
    
    Returns:
        Dict with stats (books_seeded, reviews_added, errors)
    """
    db = SessionLocal()
    stats = {
        "books_seeded": 0,
        "reviews_added": 0,
        "books_not_found": 0,
        "errors": []
    }
    
    try:
        # Get or create test user
        user_id = create_test_user_if_needed(db)
        print(f"Using user: {user_id}\n")
        
        # Seed reviews for each book
        for book_id, reviews in SAMPLE_REVIEWS.items():
            try:
                # Check if book exists
                book = db.query(Book).filter(Book.book_id == book_id).first()
                if not book:
                    print(f"⊘ Book {book_id}: NOT FOUND (skipping)")
                    stats["books_not_found"] += 1
                    continue
                
                print(f"📖 Seeding: {book.title} (ID: {book_id})")
                
                # Clear existing reviews from test user for this book (if any)
                existing = db.query(Review).filter(
                    Review.book_id == book_id,
                    Review.user_id == user_id
                ).all()
                for review in existing:
                    db.delete(review)
                
                # Add new reviews
                for idx, review_data in enumerate(reviews, 1):
                    review = Review(
                        book_id=book_id,
                        user_id=user_id,
                        rating=review_data["rating"],
                        body=review_data["body"],
                    )
                    db.add(review)
                    stats["reviews_added"] += 1
                    break  # Only add first (best) review due to unique constraint
                
                print(f"   Added {len(reviews)} reviews")
                stats["books_seeded"] += 1
                
            except Exception as e:
                stats["errors"].append(f"Book {book_id}: {str(e)}")
                print(f"   ❌ Error: {str(e)}")
        
        # Commit all reviews
        db.commit()
        
        # Print summary
        print(f"\n" + "="*80)
        print("SEEDING COMPLETE")
        print("="*80)
        print(f"Books seeded:    {stats['books_seeded']}")
        print(f"Reviews added:   {stats['reviews_added']}")
        print(f"Books not found: {stats['books_not_found']}")
        if stats['errors']:
            print(f"Errors:          {len(stats['errors'])}")
            for error in stats['errors']:
                print(f"  - {error}")
        print("="*80)
        print(f"\nNext steps:")
        print(f"  1. Build emotion profiles: python scripts/build_emotion_profiles.py")
        print(f"  2. Test recommendations via: http://localhost:8000/docs")
        print(f"     POST /api/content-based (user_id: {user_id[:8]}...)")
        print("="*80)
        
        return stats
    
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        return stats
    finally:
        db.close()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   SEEDING SAMPLE BOOK REVIEWS                              ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    seed_reviews()
