#!/usr/bin/env python3
"""
Seed mood-targeted reviews across 20 books to test all 6 mood categories.
Uses 5 fake reviewer accounts to work around the unique (user_id, book_id)
constraint — each reviewer leaves exactly one review per book.
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import SessionLocal
from app.models.review import Review
from app.models.book import Book
from app.models.user import User

MOOD_REVIEWS = {

    # ── HAPPY ───────────────────────────────────────────────────────────────

    "22609391": {  # The Wright Brothers
        "mood": "happy",
        "reviews": [
            {"rating": 5, "body": "This book made me so incredibly happy and uplifted! The Wright Brothers' story is pure joy from start to finish. Their optimism and cheerful determination are contagious. I finished it with a huge smile on my face."},
            {"rating": 5, "body": "Joyful, warm, and deeply inspiring! McCullough tells this story with such delight that you can't help feeling happy and grateful. A wonderful celebration of human ingenuity that left me feeling cheerful and hopeful."},
            {"rating": 4, "body": "Such a happy and heartwarming read. The brothers' playful spirit and genuine happiness in their work shine through every page. I felt optimistic and uplifted throughout. A feel-good history book if there ever was one."},
            {"rating": 5, "body": "I was grinning with happiness the entire time I read this. The Wright Brothers radiate joy, and McCullough captures their cheerful, good-natured personalities beautifully. Absolutely delightful and uplifting!"},
            {"rating": 4, "body": "Pure happiness and inspiration. This book celebrates human achievement in the most warm and joyful way. I felt genuinely happy and moved reading about two ordinary men who changed the world with optimism and hard work."},
        ]
    },

    "4806": {  # Longitude
        "mood": "happy",
        "reviews": [
            {"rating": 5, "body": "What a delightful and joyful little book! I was happy and charmed the entire way through. John Harrison's cheerful obsession with solving this puzzle is infectious. A warm, uplifting story of perseverance rewarded."},
            {"rating": 5, "body": "This book made me genuinely happy! The story of Harrison's triumph is told with such warmth and delight. I felt cheerful and satisfied at every turn — especially the wonderfully happy ending. A gem of popular history."},
            {"rating": 4, "body": "Joyful and charming. Sobel writes with such warm enthusiasm that her happiness about this subject leaps off the page. I was delighted and uplifted throughout. A short, sweet, feel-good history book."},
            {"rating": 5, "body": "I felt so happy finishing this! Harrison's story is one of those rare tales where the good guy wins, and Sobel tells it with infectious joy and warmth. Completely uplifting and a pleasure to read."},
        ]
    },

    "2203": {  # John Adams
        "mood": "happy",
        "reviews": [
            {"rating": 5, "body": "McCullough writes about Adams with such genuine warmth and joy that the happiness is contagious. Adams and Abigail's love story is deeply touching and uplifting. I felt cheerful and inspired throughout this wonderful biography."},
            {"rating": 4, "body": "A warm, joyful, and deeply satisfying biography. The portrait of Adams as a happy family man alongside his public life is beautifully rendered. I finished this book feeling uplifted and genuinely happy."},
            {"rating": 5, "body": "Joyful reading! McCullough's obvious delight and happiness in telling this story makes every page a pleasure. Adams comes alive as a warm, funny, deeply human figure. Uplifting and heartwarming from beginning to end."},
            {"rating": 4, "body": "This book left me feeling happy and deeply satisfied. The story of Adams' life — his joys, his family, his triumphs — is told with warmth and cheerfulness. A delightful and inspiring biography."},
        ]
    },

    "21": {  # A Short History of Nearly Everything
        "mood": "happy",
        "reviews": [
            {"rating": 5, "body": "This book made me so happy to be alive and curious! Bryson writes with infectious joy and delight about science. I was cheerful and uplifted on every single page. A wonderful, warm celebration of human knowledge."},
            {"rating": 5, "body": "Pure joy and happiness! Bryson's enthusiasm and delight in explaining the world is completely contagious. I laughed, I smiled, I felt genuinely happy and grateful. One of the most uplifting books I have ever read."},
            {"rating": 4, "body": "Such a joyful, happy read! Bryson approaches science with warm humor and cheerful curiosity. I was delighted and uplifted throughout. A feel-good book that made me happy to be a human being on this planet."},
        ]
    },

    # ── SAD ─────────────────────────────────────────────────────────────────

    "1617": {  # Night
        "mood": "sad",
        "reviews": [
            {"rating": 5, "body": "Profoundly and deeply sad. This memoir broke my heart completely. I cried throughout and felt a heavy, lingering grief long after finishing. Wiesel's account of loss and sorrow is devastating. A heartbreaking and essential book."},
            {"rating": 5, "body": "The most heartbreaking and sorrowful book I have ever read. The sadness and grief are overwhelming, but it must be read. I sobbed through much of it. A deeply moving and tragic account of unimaginable suffering."},
            {"rating": 5, "body": "Deeply, achingly sad. I felt immense sorrow and heartbreak reading this. Wiesel's grief and loss permeate every word. This book will make you weep and feel the weight of tragedy deeply. Devastating and unforgettable."},
            {"rating": 5, "body": "I was overwhelmed with sadness and grief reading this. The melancholy and heartbreak are profound. Wiesel writes about sorrow and loss with a quiet power that made me weep. Beautifully tragic and deeply moving."},
            {"rating": 5, "body": "A sorrowful, heartbreaking masterpiece. The sadness and grief in these pages are immense. I felt a deep melancholy that stayed with me for weeks. Essential reading, though emotionally devastating."},
        ]
    },

    "48855": {  # The Diary of a Young Girl
        "mood": "sad",
        "reviews": [
            {"rating": 5, "body": "Heartbreaking and deeply sad. Anne's diary moved me to tears repeatedly. The sadness of her situation and the tragedy of her fate left me feeling profound grief. A deeply sorrowful and moving account."},
            {"rating": 5, "body": "I wept reading this. The sadness and melancholy grow heavier with every entry, knowing what is coming. Anne's voice is full of hope, which makes the tragedy and grief even more devastating. Profoundly sorrowful."},
            {"rating": 5, "body": "The most heartbreaking and sad book I have ever read. Anne's grief, her longing, and ultimately her fate filled me with overwhelming sorrow. I cried deeply and felt a sadness that lingered for days after finishing."},
            {"rating": 4, "body": "Deeply sad and emotionally devastating. The melancholy in these pages is profound — the sadness of a young life cut short. I finished this book in tears and felt grief I could not shake. A moving and sorrowful classic."},
        ]
    },

    "76401": {  # Bury My Heart at Wounded Knee
        "mood": "sad",
        "reviews": [
            {"rating": 5, "body": "Deeply heartbreaking and sorrowful. This book filled me with grief and sadness on every page. The tragedy and loss are overwhelming. I cried often and felt a heavy melancholy throughout. A devastating and important book."},
            {"rating": 5, "body": "Profoundly sad. The grief and sorrow in this history are immense. I was moved to tears repeatedly by the tragedy and heartbreak of what happened. A deeply melancholy and sorrowful book that left me emotionally shattered."},
            {"rating": 4, "body": "This book broke my heart. The sadness and grief are relentless — a devastating account of tragedy and loss. I felt deep sorrow and melancholy throughout. Heartbreaking and important reading."},
            {"rating": 5, "body": "I have rarely felt such profound sadness reading a history book. The grief is immense and the tragedy is overwhelming. This sorrowful account made me weep repeatedly. A deeply heartbreaking and essential work."},
        ]
    },

    "18478222": {  # Twelve Years a Slave
        "mood": "sad",
        "reviews": [
            {"rating": 5, "body": "Heartbreaking and deeply sad. Northup's account of suffering and loss is devastating. I felt profound grief and sorrow throughout. The melancholy and tragedy of his story moved me to tears. An essential and sorrowful book."},
            {"rating": 5, "body": "I was overcome with sadness and grief reading this. The suffering and sorrow are immense. Northup writes about his heartbreak and loss with a quiet dignity that made the tragedy even more devastating. Deeply moving."},
            {"rating": 5, "body": "The most heartbreaking memoir I have read. The sadness, grief, and sorrow throughout are overwhelming. I cried deeply and felt a lingering melancholy long after finishing. A devastating and deeply sad account."},
        ]
    },

    # ── ANGRY ───────────────────────────────────────────────────────────────

    "347610": {  # King Leopold's Ghost
        "mood": "angry",
        "reviews": [
            {"rating": 5, "body": "This book made me absolutely furious and enraged. The injustice and cruelty documented here are infuriating beyond words. I was angry throughout every page. The outrage and frustration I felt were intense. A maddening and essential book."},
            {"rating": 5, "body": "I have never felt such rage and anger reading a history book. The injustice is infuriating and the atrocities documented here filled me with fury and outrage. I was frustrated and angry long after finishing. A maddening account."},
            {"rating": 5, "body": "Enraging and infuriating. This book made me furious with righteous anger. The injustice and cruelty documented here provoked intense outrage and frustration. I was livid throughout and deeply angered by every chapter."},
            {"rating": 4, "body": "I felt deep anger and fury reading this. The injustice and atrocities made me outraged and frustrated. Hochschild documents this infuriating chapter of history with clarity that only amplifies the rage. A maddening but essential read."},
            {"rating": 5, "body": "Absolutely infuriating. The injustice documented here provoked the deepest anger and outrage I have felt reading history. I was furious and frustrated throughout. A book that made me genuinely enraged — which is exactly the point."},
        ]
    },

    "29496076": {  # Killers of the Flower Moon
        "mood": "angry",
        "reviews": [
            {"rating": 5, "body": "This book made me furious and enraged. The injustice and betrayal documented here are infuriating. I felt deep anger and outrage on every page. The greed and cruelty made me livid. A maddening and important book."},
            {"rating": 5, "body": "I was filled with rage and fury throughout this book. The injustice is absolutely infuriating. Grann documents these outrages with precision that only deepens the anger. I was frustrated and enraged from beginning to end."},
            {"rating": 4, "body": "Deeply infuriating. The anger and outrage I felt reading this were intense and persistent. The injustice is maddening, the betrayals enraging. I was furious throughout and the frustration never let up. Brilliantly told and rightfully angering."},
            {"rating": 5, "body": "An infuriating and enraging book. I felt genuine fury and anger throughout — the injustice is outrageous and the cruelty maddening. This book provoked deep frustration and rage that I could not shake for days afterward."},
        ]
    },

    "2767": {  # A People's History of the United States
        "mood": "angry",
        "reviews": [
            {"rating": 5, "body": "This book made me angry and outraged in all the right ways. The injustices documented here are infuriating and the frustration is constant. Zinn fires you up with righteous anger on every page. A furious and necessary book."},
            {"rating": 4, "body": "I felt genuine anger and frustration throughout this book. The injustice is infuriating and Zinn's documentation of it provoked real outrage. I was furious and enraged reading this — which is entirely the point. An angering read."},
            {"rating": 5, "body": "Infuriating and enraging — deliberately so. The injustices documented here filled me with fury and outrage. I was angry and frustrated throughout. This book provokes the righteous anger necessary for understanding history."},
        ]
    },

    # ── EXCITED ─────────────────────────────────────────────────────────────

    "21996": {  # The Devil in the White City
        "mood": "excited",
        "reviews": [
            {"rating": 5, "body": "Absolutely thrilling and exciting! I could not put this down. The suspense and tension kept me on the edge of my seat throughout. Larson builds excitement masterfully — I was breathless and exhilarated reading this. Phenomenal!"},
            {"rating": 5, "body": "So thrilling and exciting! The dual narrative kept me riveted with suspense and adrenaline. I was on the edge of my seat the entire time. The excitement and tension never let up. A breathless, pulse-pounding read!"},
            {"rating": 4, "body": "Gripping and intensely exciting. The suspense is incredible and the tension is electric. I was thrilled and exhilarated from start to finish. Larson makes history feel like a thriller — fast, exciting, and impossible to put down."},
            {"rating": 5, "body": "This book had me breathless with excitement and suspense! The tension was incredible and I was thrilled and on the edge of my seat throughout. An exhilarating, pulse-pounding narrative that I devoured in one sitting."},
            {"rating": 4, "body": "Thrilling, exciting, and completely gripping. The suspense kept building and I was exhilarated throughout. The tension in the Holmes chapters especially had me breathless. An incredibly exciting read that I couldn't put down."},
        ]
    },

    "55403": {  # Black Hawk Down
        "mood": "excited",
        "reviews": [
            {"rating": 5, "body": "Absolutely thrilling and exhilarating! The action and suspense are incredible. I was on the edge of my seat throughout — breathless with excitement and adrenaline. Bowden writes with pulse-pounding tension that never lets up. Phenomenal!"},
            {"rating": 5, "body": "One of the most exciting and thrilling books I have ever read. The suspense is relentless and the action is breathless. I was exhilarated and riveted throughout. The tension kept building until I was completely breathless. Outstanding!"},
            {"rating": 4, "body": "Gripping and intensely exciting. The suspense never lets up and the action is thrilling. I was breathless and exhilarated from start to finish. This book had me on the edge of my seat the entire time. Incredibly exciting reading."},
            {"rating": 5, "body": "So thrilling and exciting! I was breathless with suspense throughout. The action is pulse-pounding and the tension is electrifying. Bowden creates an exhilarating account that had me riveted and on the edge of my seat from the first page."},
        ]
    },

    "139069": {  # Endurance
        "mood": "excited",
        "reviews": [
            {"rating": 5, "body": "Absolutely thrilling and exciting! Shackleton's survival story is one of the most exhilarating adventures ever written. The suspense and tension kept me breathless and on the edge of my seat throughout. Riveting and electrifying!"},
            {"rating": 5, "body": "I have never felt such excitement and exhilaration reading a true story. The suspense is incredible and the action is thrilling. I was breathless throughout and on the edge of my seat the entire time. A pulse-pounding adventure!"},
            {"rating": 5, "body": "Thrilling, exciting, and completely breathless! The suspense builds relentlessly and the adventure is exhilarating. I was riveted and on the edge of my seat from start to finish. The most exciting true survival story ever told!"},
            {"rating": 4, "body": "An incredibly exciting and thrilling adventure. The suspense is heart-stopping and I was breathless with exhilaration throughout. The tension and action kept me riveted and on the edge of my seat. A magnificent, exciting read."},
        ]
    },

    # ── ROMANTIC ────────────────────────────────────────────────────────────

    "7968243": {  # Cleopatra: A Life
        "mood": "romantic",
        "reviews": [
            {"rating": 5, "body": "Deeply romantic and passionately told! Schiff brings Cleopatra's love affairs and passionate relationships to life beautifully. The romance between her and Antony is tender and deeply moving. A lush, romantic, and sensual biography."},
            {"rating": 5, "body": "What a romantic and passionate biography! The love stories are beautifully rendered — tender, sensual, and deeply moving. I was swept up in the romance and passion on every page. A wonderfully romantic and intimate portrait."},
            {"rating": 4, "body": "Lush, romantic, and deeply passionate. Schiff writes about Cleopatra's loves and relationships with warmth and tenderness. The romantic elements are beautifully handled and I was moved by the passion and intimacy throughout."},
            {"rating": 5, "body": "Such a romantic and tender biography! The passionate love stories are beautifully told — sensual, moving, and deeply intimate. I was swept away by the romance and felt warmly moved throughout. A gorgeous, romantic read."},
            {"rating": 4, "body": "Wonderfully romantic and passionately written. The love affairs and intimate relationships are portrayed with tenderness and warmth. I was deeply moved by the romance and passion throughout this beautiful, intimate biography."},
        ]
    },

    "17157": {  # Marie Antoinette
        "mood": "romantic",
        "reviews": [
            {"rating": 5, "body": "Beautifully romantic and deeply tender! Fraser portrays Marie Antoinette's relationships and romantic life with warmth and intimacy. The love and passion in this biography are deeply moving. A lush, romantic, and touching portrait."},
            {"rating": 5, "body": "So romantic and passionately told! The tender love stories and intimate relationships are beautifully rendered. I was swept up in the romance and passion throughout. A warm, lush, and deeply romantic biography."},
            {"rating": 4, "body": "A deeply romantic and tender biography. The love and passion in Marie Antoinette's life are portrayed with warmth and intimacy. I was moved by the romantic elements and felt a tender connection to her throughout."},
            {"rating": 5, "body": "Lush, romantic, and deeply moving. Fraser brings the passionate relationships and tender loves of Marie Antoinette's life to vivid reality. The romance is beautifully handled and I was swept away by the warmth and intimacy."},
            {"rating": 4, "body": "Such a romantic and beautifully tender book! The passion and intimacy of Marie Antoinette's relationships are portrayed with warmth and deep feeling. I was moved by the romance throughout and felt the love in every chapter."},
        ]
    },

    "319300": {  # Georgiana: Duchess of Devonshire
        "mood": "romantic",
        "reviews": [
            {"rating": 5, "body": "So wonderfully romantic and passionately written! Georgiana's love affairs and passionate relationships are portrayed with warmth and tender intimacy. I was swept away by the romance and passion. A deeply romantic and moving biography."},
            {"rating": 5, "body": "A beautifully romantic biography! The love stories and passionate relationships are rendered with tenderness and intimacy. I was deeply moved by the romance throughout and felt warmly drawn to Georgiana. Lush and passionately told."},
            {"rating": 4, "body": "Deeply romantic and passionately told. The tender love affairs and intimate relationships make this biography feel like a beautiful love story. I was swept up in the romance and felt the passion and warmth on every page."},
            {"rating": 5, "body": "What a romantic and tender portrait! The passion and intimacy of Georgiana's relationships are beautifully rendered. I was moved by the love stories and felt warmly swept away by the romance throughout. A wonderful, romantic biography."},
        ]
    },

    # ── ADVENTUROUS ─────────────────────────────────────────────────────────

    "174354": {  # Over the Edge of the World: Magellan
        "mood": "adventurous",
        "reviews": [
            {"rating": 5, "body": "A breathtaking adventure! The daring, exploration, and boldness of Magellan's voyage filled me with a sense of adventure and wanderlust. I felt the thrill of discovery on every page. An exhilarating journey of exploration and daring courage."},
            {"rating": 5, "body": "What an incredible adventure! The daring spirit of exploration and the thrill of venturing into the unknown are captured perfectly. I was filled with wanderlust and the joy of discovery throughout. An exhilarating and daring read!"},
            {"rating": 4, "body": "Thrilling adventure from start to finish! The daring exploration and bold courage of the voyage are wonderfully conveyed. I felt the spirit of adventure and discovery on every page. A joyful and exhilarating account of exploration."},
            {"rating": 5, "body": "Such an exciting adventure! The boldness and daring spirit of exploration are captured beautifully. I was filled with wanderlust and the thrill of discovery throughout. A magnificent, adventurous journey that I could not put down."},
            {"rating": 4, "body": "Pure adventure and exploration! The daring and boldness of this voyage filled me with a spirit of discovery and wanderlust. I was thrilled by the adventure on every page. An exhilarating account of one of history's greatest explorations."},
        ]
    },

    "78508": {  # The River of Doubt
        "mood": "adventurous",
        "reviews": [
            {"rating": 5, "body": "An incredible adventure! The daring exploration of the Amazon filled me with excitement and a sense of wonder. The bold spirit of discovery and adventure are wonderfully conveyed. I was thrilled by the exploration on every page. Exhilarating!"},
            {"rating": 5, "body": "What a daring and exciting adventure! The exploration of the unknown river is filled with bold courage and the spirit of discovery. I was exhilarated and filled with wanderlust throughout. A magnificent adventure tale!"},
            {"rating": 4, "body": "Thrilling adventure and exploration! The daring and boldness of Roosevelt's Amazon journey are perfectly captured. I felt the thrill of discovery and adventure on every page. A wonderful, exciting account of bold exploration."},
            {"rating": 5, "body": "Pure adventure and daring exploration! The spirit of discovery and bold courage filled me with excitement and wanderlust throughout. I was exhilarated on every page. A breathtaking and wonderfully adventurous read."},
        ]
    },

    "45546": {  # Undaunted Courage
        "mood": "adventurous",
        "reviews": [
            {"rating": 5, "body": "A magnificent adventure! The bold exploration and daring spirit of discovery are captured brilliantly. I was filled with wanderlust and the thrill of adventure throughout. The courage and excitement of the journey are wonderfully conveyed. Exhilarating!"},
            {"rating": 5, "body": "What a daring and exciting adventure! The exploration and bold spirit of discovery are beautifully told. I felt the thrill and excitement of adventure on every page. A wonderful account of daring exploration and courageous discovery."},
            {"rating": 4, "body": "Thrilling adventure and exploration from beginning to end! The daring and boldness of Lewis and Clark are perfectly conveyed. I was filled with wanderlust and the joy of discovery throughout. An exciting and exhilarating adventure read."},
            {"rating": 5, "body": "Pure adventure! The daring exploration and bold spirit of discovery filled me with excitement and wanderlust. I was exhilarated and thrilled throughout. A wonderful, adventurous account that celebrates the daring spirit of exploration beautifully."},
        ]
    },

    "270032": {  # Seven Years in Tibet
        "mood": "adventurous",
        "reviews": [
            {"rating": 5, "body": "A wonderful adventure! The daring journey and spirit of exploration are beautifully conveyed. I felt the thrill and excitement of discovery on every page. The boldness of the adventure filled me with wanderlust and joy. Exhilarating reading!"},
            {"rating": 4, "body": "Such a daring and exciting adventure! The exploration and bold spirit of discovery are wonderfully captured. I was filled with wanderlust and the thrill of adventure throughout. A beautiful account of daring exploration and discovery."},
            {"rating": 5, "body": "An incredible adventure and journey of discovery! The daring and boldness are perfectly captured. I felt the excitement and thrill of exploration on every page. This book filled me with wanderlust and the joy of adventure."},
            {"rating": 4, "body": "Thrilling adventure and exploration! The spirit of daring discovery and bold courage are beautifully conveyed. I was filled with wanderlust and excitement throughout. A wonderful adventurous read about an extraordinary journey."},
        ]
    },
}

# 5 reviewer personas — each leaves one review per book
REVIEWER_EMAILS = [
    "reviewer_1@moodtest.com",
    "reviewer_2@moodtest.com",
    "reviewer_3@moodtest.com",
    "reviewer_4@moodtest.com",
    "reviewer_5@moodtest.com",
]


def get_or_create_reviewers(db) -> list:
    """Get or create 5 reviewer accounts, return list of user_ids."""
    user_ids = []
    for email in REVIEWER_EMAILS:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                user_id=str(uuid.uuid4()),
                cognito_sub=str(uuid.uuid4()),
                email=email,
            )
            db.add(user)
            db.flush()
            print(f"  ✓ Created reviewer: {email}")
        user_ids.append(user.user_id)
    db.commit()
    return user_ids


def seed():
    db = SessionLocal()
    stats = {"books_seeded": 0, "reviews_added": 0, "books_not_found": 0, "errors": []}

    try:
        reviewer_ids = get_or_create_reviewers(db)
        print(f"\nUsing {len(reviewer_ids)} reviewer accounts.\n")

        mood_counts = {}

        for book_id, data in MOOD_REVIEWS.items():
            mood = data["mood"]
            reviews = data["reviews"]

            try:
                book = db.query(Book).filter(Book.book_id == book_id).first()
                if not book:
                    print(f"  ⊘  [{mood:>12}]  Book {book_id} NOT FOUND — skipping")
                    stats["books_not_found"] += 1
                    continue

                # Delete existing reviews for this book from our reviewers, then flush
                db.query(Review).filter(
                    Review.book_id == book_id,
                    Review.user_id.in_(reviewer_ids)
                ).delete(synchronize_session=False)
                db.flush()

                # One review per reviewer (max 5)
                for i, review_data in enumerate(reviews[:5]):
                    review = Review(
                        book_id=book_id,
                        user_id=reviewer_ids[i],
                        rating=review_data["rating"],
                        body=review_data["body"],
                    )
                    db.add(review)
                    stats["reviews_added"] += 1

                db.flush()  # surface constraint errors per book, not at batch end
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
                stats["books_seeded"] += 1
                print(f"  ✓  [{mood:>12}]  {book.title[:60]}")

            except Exception as e:
                db.rollback()
                stats["errors"].append(f"Book {book_id}: {e}")
                print(f"  ✗  [{mood:>12}]  Book {book_id} ERROR: {e}")

        db.commit()

        print(f"\n{'='*70}")
        print("SEEDING COMPLETE")
        print(f"{'='*70}")
        print(f"  Books seeded   : {stats['books_seeded']}")
        print(f"  Reviews added  : {stats['reviews_added']}")
        print(f"  Books not found: {stats['books_not_found']}")
        print(f"\n  Coverage per mood:")
        for mood, count in sorted(mood_counts.items()):
            print(f"    {mood:>12} : {count} book(s)")
        if stats["errors"]:
            print(f"\n  Errors ({len(stats['errors'])}):")
            for e in stats["errors"]:
                print(f"    - {e}")
        print(f"{'='*70}\n")

    except Exception as e:
        db.rollback()
        print(f"✗ Fatal error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║         SEEDING MOOD-TARGETED BOOK REVIEWS (multi-reviewer)         ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    seed()