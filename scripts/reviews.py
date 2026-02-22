import sys
from pathlib import Path
from datetime import datetime
import uuid

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import SessionLocal
from app.models.review import Review


def seed_reviews():
    db = SessionLocal()

    # Current timestamp (without microseconds)
    now = datetime.now().replace(microsecond=0)

    # Seed data
    reviews_data = [
        {"book_id": 2203, "rating": 4, "title": "Great Book!", "body": "I really enjoyed reading this book. The storyline was gripping."},
        {"book_id": 2368, "rating": 5, "title": "Amazing Read", "body": "This book exceeded my expectations. Highly recommend!"},
        {"book_id": 1067, "rating": 3, "title": "Good, but not great", "body": "It was interesting but lacked depth in some areas."},
        {"book_id": 4806, "rating": 2, "title": "Disappointing", "body": "I expected more from this book."},
        {"book_id": 2715, "rating": 4, "title": "Worth the Read", "body": "Solid book overall. Would recommend."},
    ]

    user_id = "7f18e4e9-6f1c-4177-b6ce-01233b2e82c1"

    inserted_count = 0

    for data in reviews_data:
        # Check if this user already has a review for this book
        exists = db.query(Review).filter_by(user_id=user_id, book_id=data["book_id"]).first()
        if exists:
            print(f"Review for book {data['book_id']} already exists. Skipping.")
            continue

        review = Review(
            review_id=str(uuid.uuid4()),
            user_id=user_id,
            book_id=data["book_id"],
            rating=data["rating"],
            title=data["title"],
            body=data["body"],
            created_at=now,
            updated_at=now
        )

        db.add(review)
        inserted_count += 1

        # Print inserted review with clean timestamp
        print(f"Inserted review: {review.title}, Created at: {review.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

    db.commit()
    db.close()

    print(f"Reviews inserted.")


if __name__ == "__main__":
    seed_reviews()




# Clear Reviews in DB

# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent))

# from app.db.database import SessionLocal
# from app.models.review import Review

# db = SessionLocal()
# db.query(Review).filter(Review.user_id=="7f18e4e9-6f1c-4177-b6ce-01233b2e82c1").delete()
# db.commit()
# db.close()
# print("Reviews cleared for user")



