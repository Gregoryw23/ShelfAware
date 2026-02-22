# Goodreads Review Import Workflow

This guide explains how to import reviews from Goodreads and build emotion profiles for the recommendation system.

## Architecture

```
Goodreads Export (CSV)
      ↓
import_goodreads_reviews.py  ← Parse & validate CSV
      ↓                         ← Insert into Review table
Database (reviews)
      ↓
build_emotion_profiles.py    ← Extract emotions from review text
      ↓                         ← Create emotion profiles
Emotion Profiles (for recommendation engine)
      ↓
RecommendationEngine         ← Uses emotion profiles for:
  - content-based (similar emotional tone)
  - collaborative (similar emotional preferences)
  - mood-based (future)
```

## Quick Start

### Step 1: Export Reviews from Goodreads

```bash
# Show detailed instructions
python scripts/import_goodreads_reviews.py --instructions
```

Or manually:
1. Visit: https://www.goodreads.com/review/import_export
2. Sign in & click "Export" under "Import/Export" section
3. Save the downloaded CSV file locally

### Step 2: Import Reviews into Database

```bash
# Import your Goodreads CSV
python scripts/import_goodreads_reviews.py \
  --csv path/to/goodreads_export.csv \
  --user your_user_id
```

Expected output:
```
✓ Found user: user_123
✓ CSV columns: ['...', 'book_id', 'rating', 'review_text', '...']
✓ Successfully imported 42 reviews
⊘ Skipped 3 duplicate/incomplete reviews
❌ 1 error encountered
```

**What happens:**
- CSV is validated (required columns: book_id, rating, review_text)
- Books are matched against your database
- Reviews are inserted into `Review` table
- Mood entries are created for non-empty reviews
- Duplicates are skipped (same user + book)

### Step 3: Build Emotion Profiles

```bash
# Process all books and extract emotions from reviews
python scripts/build_emotion_profiles.py

# Or limit to first 50 books for testing
python scripts/build_emotion_profiles.py --limit 50

# View emotion categories
python scripts/build_emotion_profiles.py --info
```

Expected output:
```
Processing 150 books...

[1/150] The Great Gatsby: 5 reviews analyzed
             Top emotions: excited(12.5), romantic(8.2), dark(3.1)

[2/150] 1984: 8 reviews analyzed
             Top emotions: dark(18.3), angry(12.1), scared(9.7)
...

EMOTION PROFILE BUILD SUMMARY
═════════════════════════════════════════
Books processed:          145
Reviews analyzed:         523
Books without reviews:    5
Emotion profiles created: 145
═════════════════════════════════════════
```

**What happens:**
- Emotion extractor analyzes all review text
- 8 emotions tracked: happy, sad, angry, excited, scared, romantic, suspenseful, dark
- Emotion scores aggregated per book
- Profiles stored for recommendation engine

### Step 4: Test Recommendations

The recommendation engine now has emotion profiles to work with:

```bash
# Via command line (requires data in database)
curl -X POST http://localhost:8000/api/content-based \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "book_id": "b001",
    "rating": 5,
    "review_text": "Amazing! Absolutely loved this book."
  }'

# Or use Swagger UI:
# Visit http://localhost:8000/docs
# Navigate to POST /api/content-based
# Click "Try it out" and enter your test data
```

## CSV Format Reference

### Goodreads Export CSV (Standard)

| Column          | Required | Example |
|-----------------|----------|---------|
| book_id         | Yes      | `"54" ` |
| title           | No       | `"The Great Gatsby"` |
| author          | No       | `"F. Scott Fitzgerald"` |
| my_rating       | Yes      | `5` |
| my_review       | No       | `"Absolutely wonderful!"` |
| date_read       | No       | `"2024/01/15"` |

### Minimal Custom CSV

If you create your own CSV:

```csv
book_id,rating,review_text
"b001",5,"Amazing book! Loved every moment."
"b002",4,"Good but slow pacing in parts."
"b003",3,"Average, didn't connect with characters."
```

**Requirements:**
- `book_id`: Must match a book in your database (check [Debug Endpoints](#debug-endpoints) section)
- `rating`: Integer 1-5
- `review_text`: Any text (can be empty, but reviews without text won't contribute to emotion profiles)

## Troubleshooting

### Issue: "Book ID 'xyz' not found"

**Cause:** The Goodreads book_id doesn't exist in your ShelfAware database

**Solution:**
1. Check what books are in your database:
   ```bash
   curl http://localhost:8000/api/debug/books
   ```
2. Update the book_id in your CSV to match a real book_id
3. Or add missing books to your database first

### Issue: Low import success rate

**Check:**
```bash
# View all books in database
curl http://localhost:8000/api/debug/books

# View specific book's reviews
curl http://localhost:8000/api/debug/book/b001/reviews

# Check a user's shelf
curl http://localhost:8000/api/debug/user/user_123/bookshelf
```

### Issue: Emotion profiles don't show up

**Possible causes:**
1. Reviews imported but text is empty
2. Emotion lexicon doesn't match review vocabulary
3. Emotion profile column not defined in Book model

**Solution:**
```bash
# Check if reviews were actually imported
curl http://localhost:8000/api/debug/book/b001/reviews

# Run emotion profile build with verbose output
python scripts/build_emotion_profiles.py --limit 10
```

## Debug Endpoints

All endpoints return JSON data for inspection:

### GET /api/debug/books
List all books in database
```bash
curl http://localhost:8000/api/debug/books
```

Response:
```json
{
  "total_books": 150,
  "books": [
    {"book_id": "b001", "title": "The Great Gatsby"},
    {"book_id": "b002", "title": "1984"}
  ]
}
```

### GET /api/debug/user/{user_id}/bookshelf
View user's shelf with read books
```bash
curl http://localhost:8000/api/debug/user/user_123/bookshelf
```

### GET /api/debug/book/{book_id}/reviews
View all reviews for a book
```bash
curl http://localhost:8000/api/debug/book/b001/reviews
```

### GET /api/debug/book/{book_id}/emotions
View emotion profile for a book
```bash
curl http://localhost:8000/api/debug/book/b001/emotions
```

## Emotion Categories

The system recognizes 8 emotional dimensions:

| Emotion       | Keywords |
|---------------|----------|
| **happy**     | joy, love, wonderful, amazing, brilliant, delighted |
| **sad**       | sad, depressed, disappointing, boring, waste, melancholy |
| **angry**     | angry, infuriating, frustrated, hate, terrible, enraged |
| **excited**   | excited, thrilled, thrilling, suspenseful, gripping, electrifying |
| **scared**    | scared, horror, creepy, haunted, terrifying, chilling |
| **romantic**  | romantic, love, tenderness, touching, emotional, intimate |
| **suspenseful** | suspenseful, mystery, twists, page turner, thriller, mystery |
| **dark**      | dark, grim, evil, death, tragic, bleak |

These are used by the recommendation engine to match books with similar emotional tones.

## Integration with Recommendation Engine

After building emotion profiles, recommendations work like this:

### Content-Based (Similar Books)
```
User reads Book A (emotional profile: exciting, dark, romantic)
          ↓
System finds other books with similar emotional profiles
          ↓
Returns ranked recommendations (Book B, Book C, etc.)
```

### Collaborative (Similar Users)
```
User A's reviews → emotion preferences (loves exciting + romantic)
User B's reviews → emotion preferences (similar to User A)
          ↓
System finds books User B loved that User A hasn't read
          ↓
Returns ranked recommendations
```

## Advanced Usage

### Rebuild All Emotion Profiles
```bash
# Full rebuild of all emotion profiles
# (Use after importing new reviews)
python scripts/build_emotion_profiles.py
```

### Test Import Without Committing
```bash
# (Modify script to print-only before uncommenting db.commit())
# Useful for validating CSV format before importing
```

### Export Recommendations
```bash
# Future feature: export as CSV after running recommendations
# python scripts/export_recommendations.py --user user_123 --output recommendations.csv
```

## Notes

- ✅ **Safe approach**: Goodreads export is manual (respects ToS)
- ✅ **Flexible**: Accepts various CSV formats with smart column detection
- ✅ **Robust**: Validates ratings, skips duplicates, handles errors gracefully
- ❌ **Scraping**: Web scraping Goodreads is against their ToS and commonly blocked

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Run debug endpoints to inspect data
3. Check uvicorn logs: `tail -f uvicorn.log`
