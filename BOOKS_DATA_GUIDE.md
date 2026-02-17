# Books Data Loading Guide

## Overview

The ShelfAware project now includes a comprehensive books dataset with 245 books and their genres, loaded from the `BooksDB_wGenres.csv` file.

## What's Included

- **245 Books**: Complete bibliography with titles, subtitles, cover images, abstracts, page counts, and publication dates
- **Genre Associations**: Many-to-many relationships between books and genres for flexible categorization
- **Database Schema**: New `book_genre` join table for managing genre relationships

## For Team Members

### Setting Up the Database (One-time)

1. **Install dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Load the books data into your local SQLite database**:
   ```bash
   python scripts/load_books_data.py
   ```

   This will:
   - Read the CSV file with proper UTF-8 encoding handling
   - Create the SQLite database (`app.db`) if it doesn't exist
   - Create all necessary tables including the new `book_genre` join table
   - Import 245 books with their genres
   - Insert genre entries and create book-genre associations

3. **Verify the data loaded successfully**:
   ```python
   from app.db.database import SessionLocal
   from app.models.book import Book
   
   db = SessionLocal()
   book_count = db.query(Book).count()
   print(f"Total books in database: {book_count}")  # Should print: 245
   ```

### Database Structure

#### Book Model
- `book_id` (String, Primary Key): Unique identifier
- `title` (String): Book title
- `subtitle` (String, Optional): Book subtitle
- `cover_image_url` (String, Optional): Cover image URL
- `abstract` (String, Optional): Book description/synopsis
- `CommunitySynopsis` (String, Optional): Community-generated synopsis
- `page_count` (Integer, Optional): Number of pages
- `published_date` (Date, Optional): Publication date
- `created_at` (DateTime): When the book was added to the database

#### Genre Model
- `genre_id` (Integer, Primary Key): Unique identifier
- `name` (String): Genre name (e.g., "Biography/Memoir", "Military History")

#### book_genre Join Table
- Connects books to genres with many-to-many relationship
- Primary key: (book_id, genre_id) composite

### CSV Format

The source data (`BooksDB_wGenres.csv`) contains:
- `book_id`: Goodreads book ID
- `title`: Book title
- `subtitle`: Book subtitle (optional)
- `cover_image_url`: URL to book cover image
- `abstract`: Book description from Goodreads
- `CommunityReview`: Maps to `CommunitySynopsis` in the database
- `page_count`: Number of pages
- `published_date`: Publication date (format: "Month DD, YYYY")
- `Genre`: Comma/slash-separated list of genres

### Data Notes

- The CSV encoding includes a UTF-8 BOM (Byte Order Mark), which is handled automatically by the loading script
- Missing or incomplete rows are skipped with a warning message
- Genres are automatically deduplicated - no duplicate genre entries are created
- The database file (`app.db`) is in `.gitignore` and should not be committed to version control

### Running the Application

After loading the data:
```bash
uvicorn app.main:app --reload
```

The books will be accessible via the API endpoints and can be used in book-related operations.

## Future Tasks

- Adding author information and author-book relationships
- Integrating Chroma vector database for semantic search
- Building recommendation engine using community synopses
- Expanding genre classification system

## Support

If you encounter any issues loading the data:
1. Ensure Python 3.8+ is installed
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Check that `BooksDB_wGenres.csv` is in the project root directory
4. Run with verbose output: `python scripts/load_books_data.py` (shows all SQL operations)
