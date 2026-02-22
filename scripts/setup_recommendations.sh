#!/bin/bash
#
# Quick setup script to populate the database with sample reviews and build emotion profiles
#
# Usage: bash scripts/setup_recommendations.sh
#
# This script:
# 1. Adds sample reviews from 5 biography/history books
# 2. Builds emotion profiles from those reviews
# 3. Enables testing the recommendation endpoints
#

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║            SETTING UP RECOMMENDATIONS WITH SAMPLE DATA                     ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python venv exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠ No virtual environment found. Make sure dependencies are installed:"
    echo "  pip install -r requirements.txt"
    echo ""
fi

# Step 1: Seed sample reviews
echo "Step 1: Seeding sample reviews into database..."
echo "─────────────────────────────────────────────────"
python scripts/seed_sample_reviews.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Failed to seed reviews. Make sure:"
    echo "   1. Virtual environment is activated"
    echo "   2. Dependencies are installed: pip install -r requirements.txt"
    echo "   3. Database exists at app.db"
    exit 1
fi

echo ""
echo "Step 2: Building emotion profiles..."
echo "────────────────────────────────────"
python scripts/build_emotion_profiles.py

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                       SETUP COMPLETE!                                      ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Start the server: uvicorn app.main:app --reload"
echo "  2. Open Swagger UI: http://localhost:8000/docs"
echo "  3. Test recommendations:"
echo "     - POST /api/content-based (similar books by emotion)"
echo "     - POST /api/collaborative (books liked by similar users)"
echo "  4. Use debug endpoints:"
echo "     - GET /api/debug/books (list all books)"
echo "     - GET /api/debug/book/{id}/reviews (see reviews for a book)"
echo "     - GET /api/debug/book/{id}/emotions (see emotion profile)"
echo ""
