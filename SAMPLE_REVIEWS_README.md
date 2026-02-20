# Sample Review Seeding & Import Scripts

This directory contains scripts for populating the ShelfAware database with reviews for testing the recommendation engine.

## Scripts

### 1. seed_sample_reviews.py
**Purpose**: Quickly add realistic sample reviews to specific books in the database for testing.

**Books Seeded**:
- Book ID: 6462 (George Washington biography)
- Book ID: 93996 (Hitler biography)  
- Book ID: 1206073 (Washington's Crossing)
- Book ID: 2368 (Mornings on Horseback)
- Book ID: 10335318 (Destiny of the Republic)

**Features**:
- Adds 6-7 sample reviews per book
- Varied ratings (1-5 stars)
- Diverse emotional content (happy, sad, dark, excited, romantic, suspenseful)
- Realistic for history/biography genre
- Creates test user if needed
- No external dependencies (uses existing models)

**Usage**:
```bash
python scripts/seed_sample_reviews.py
```

**Output**:
```
SEEDING SAMPLE BOOK REVIEWS
════════════════════════════════════════════════════════════════════════════

✓ Created test user: 550e8400-e29b-41d4-a716-446655440000
Using user: 550e8400-e29b-41d4-a716-446655440000

📖 Seeding: George Washington (ID: 6462)
   Added 7 reviews
📖 Seeding: Hitler: A Biography (ID: 93996)
   Added 6 reviews
📖 Seeding: Washington's Crossing (ID: 1206073)
   Added 7 reviews
📖 Seeding: Mornings on Horseback (ID: 2368)
   Added 7 reviews
📖 Seeding: Destiny of the Republic (ID: 10335318)
   Added 7 reviews

════════════════════════════════════════════════════════════════════════════
SEEDING COMPLETE
════════════════════════════════════════════════════════════════════════════
Books seeded:    5
Reviews added:   34
Books not found: 0
════════════════════════════════════════════════════════════════════════════

Next steps:
  1. Build emotion profiles: python scripts/build_emotion_profiles.py
  2. Test recommendations via: http://localhost:8000/docs
     POST /api/content-based (user_id: 550e8400...)
════════════════════════════════════════════════════════════════════════════
```

---

### 2. import_goodreads_reviews.py
**Purpose**: Import your own Goodreads reviews from a CSV file into ShelfAware.

**Why CSV Instead of Scraping?**
- ✅ Respects Goodreads' Terms of Service
- ✅ More reliable (no HTML parsing required)
- ✅ Goodreads officially supports CSV export
- ❌ Scraping is against ToS and commonly blocked

**How to Export from Goodreads**:
1. Visit: https://www.goodreads.com/review/import_export
2. Sign in if needed
3. Click "Export" button (exports all your reviews as CSV)
4. Save the file locally

**CSV Format**:
The script supports multiple column name variations:

| Required | Optional |
|----------|----------|
| `book_id` (or `id`, `bookid`) | `title` |
| `rating` (or `my_rating`) | `author` |
| `review_text` (or `review`, `my_review`) | `date_read` |

**Minimal CSV Example**:
```csv
book_id,rating,review_text
"6462",5,"Amazing biography of Washington"
"93996",4,"Important but dark historical work"
"1206073",5,"Thrilling account of the crossing"
```

**Usage**:
```bash
# Import your Goodreads export CSV
python scripts/import_goodreads_reviews.py \
  --csv path/to/my_goodreads_export.csv \
  --user your_user_id
```

**Output**:
```
Importing reviews from: path/to/my_goodreads_export.csv
User ID: your_user_id

✓ Found user: your_user_id
✓ CSV columns: ['book_id', 'title', 'author', 'rating', 'review_text', 'date_read']

✓ Successfully imported 42 reviews
⊘ Skipped 3 duplicate/incomplete reviews
❌ 2 errors encountered
   Row 15: Book ID 'xyz' not found
   Row 22: Invalid rating 'N/A'

════════════════════════════════════════════════════════════════════════════
IMPORT SUMMARY
════════════════════════════════════════════════════════════════════════════
Success:  42 reviews imported
Skipped:  3 duplicates/incomplete
Errors:   2 failed
════════════════════════════════════════════════════════════════════════════
```

---

### 3. build_emotion_profiles.py
**Purpose**: Extract emotions from all reviews and create profiles for the recommendation engine.

**Already exists** in scripts directory. Process reviews to generate emotion profiles used by:
- Content-based recommendations (similar emotional tone)
- Collaborative recommendations (similar emotional preferences)

**Usage**:
```bash
# Build profiles for all books
python scripts/build_emotion_profiles.py

# Or limit to first 50 books for testing
python scripts/build_emotion_profiles.py --limit 50

# View emotion categories
python scripts/build_emotion_profiles.py --info
```

---

## Workflow: Complete Example

### Setup Recommendations in 2 Steps

**Option A: Quick Testing (Sample Data)**
```bash
# Step 1: Add sample reviews
python scripts/seed_sample_reviews.py

# Step 2: Build emotion profiles
python scripts/build_emotion_profiles.py

# Step 3: Test via Swagger UI at http://localhost:8000/docs
```

**Option B: Your Own Data (Goodreads)**
```bash
# Step 1: Export from Goodreads (manual)
# Visit: https://www.goodreads.com/review/import_export

# Step 2: Import into ShelfAware
python scripts/import_goodreads_reviews.py \
  --csv goodreads_export.csv \
  --user your_user_id

# Step 3: Build emotion profiles
python scripts/build_emotion_profiles.py

# Step 4: Test via Swagger UI
```

---

## Architecture

```
Sample Reviews / CSV Export
          ↓
seed_sample_reviews.py  ←  or  ← import_goodreads_reviews.py
          ↓                       
Database (Review table)
          ↓
build_emotion_profiles.py
          ↓
Emotion Profiles (for books)
          ↓
RecommendationEngine
  - Content-based (similar books)
  - Collaborative (similar users)
  - Future: Mood-based
```

---

## Testing Recommendations

After seeding reviews and building emotion profiles:

```bash
# 1. Start the server
uvicorn app.main:app --reload

# 2. Open Swagger UI
# Visit: http://localhost:8000/docs

# 3. Test endpoints

# POST /api/content-based
# Find books similar to one the user reviews positively
curl -X POST http://localhost:8000/api/content-based \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_id_here",
    "book_id": "6462",
    "rating": 5,
    "review_text": "Amazing biography of Washington!"
  }'

# POST /api/collaborative
# Find books liked by users with similar tastes
curl -X POST http://localhost:8000/api/collaborative \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_id_here",
    "book_id": "6462",
    "review_text": "Absolutely brilliant leadership story!"
  }'

# Debug endpoints (inspect data)
curl http://localhost:8000/api/debug/books
curl http://localhost:8000/api/debug/book/6462/reviews
curl http://localhost:8000/api/debug/book/6462/emotions
```

---

## Emotion Categories

The recommendation system recognizes 8 emotions:

| Emotion | Example Keywords |
|---------|------------------|
| **happy** | joy, love, wonderful, amazing, brilliant, delighted |
| **sad** | sad, depressed, disappointing, boring, waste, melancholy |
| **angry** | angry, infuriating, frustrated, hate, terrible, enraged |
| **excited** | excited, thrilled, thrilling, suspenseful, gripping, electrifying |
| **scared** | scared, horror, creepy, haunted, terrifying, chilling |
| **romantic** | romantic, love, tenderness, touching, emotional, intimate |
| **suspenseful** | suspenseful, mystery, twists, page turner, thriller |
| **dark** | dark, grim, evil, death, tragic, bleak |

---

## Troubleshooting

### "Book ID 'xyz' not found"
**Cause**: Book doesn't exist in your database
**Solution**: 
- Check available books: `curl http://localhost:8000/api/debug/books`
- Use correct book IDs or add missing books first

### "User 'xyz' not found" (import script)
**Cause**: User ID doesn't exist in database
**Solution**:
- Create user first via `/api/auth/register` endpoint
- Or use the user_id from seed script output

### Low import success rate
**Check**:
```bash
# See what's in your CSV
head -5 path/to/goodreads_export.csv

# Check if books exist
curl http://localhost:8000/api/debug/books

# View reviews for a specific book
curl http://localhost:8000/api/debug/book/6462/reviews
```

### No emotion profiles generated
**Check**:
```bash
# Make sure reviews were imported
curl http://localhost:8000/api/debug/book/6462/reviews

# Run profile build with verbose output
python scripts/build_emotion_profiles.py --limit 5
```

---

## Requirements

The scripts require the ShelfAware project dependencies:
- SQLAlchemy (database ORM)
- Python 3.8+
- All packages in `requirements.txt`

Before running:
```bash
pip install -r requirements.txt
```

---

## Notes

- **Sample data**: Seeded reviews use realistic biography/history content
- **Test user**: Created automatically if needed (username: "test_user")
- **Duplicates**: Import scripts skip duplicate reviews (same user + book)
- **Safety**: CSV import respects Goodreads ToS; scraping does not
- **Emotion extraction**: Uses lexicon-based matching (no external ML models)

---

## Next Steps

After setting up reviews:
1. ✅ Test content-based recommendations (emotional similarity)
2. ✅ Test collaborative recommendations (user similarity)
3. 📋 Implement mood-based recommendations
4. 📋 Implement user preference analysis
5. 📋 Build hybrid recommendation system
