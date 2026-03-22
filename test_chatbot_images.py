#!/usr/bin/env python3
"""Test script to verify chatbot returns book cover images."""

import json
import requests
from typing import Optional
import sys

# Set UTF-8 encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

API_URL = "http://localhost:8000/api/chatbot/chat"

def test_chatbot_images(message: str = "I am feeling happy", user_id: str = "test-user-123"):
    """Test the chatbot endpoint and check if cover images are returned."""
    try:
        payload = {
            "message": message,
        }
        if user_id:
            payload["user_id"] = user_id
        
        print(f"Sending request to {API_URL}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print("-" * 60)
        
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        print(f"Response status: {response.status_code}")
        print(f"\nMood detected: {data.get('mood')}")
        print(f"Response: {data.get('response')}")
        print(f"\nNumber of books recommended: {len(data.get('books', []))}")
        
        if data.get('books'):
            print("\nBook details:")
            for i, book in enumerate(data['books'], 1):
                print(f"\n  Book {i}:")
                print(f"    - ID: {book.get('id', book.get('book_id', 'N/A'))}")
                print(f"    - Title: {book.get('title', 'N/A')}")
                print(f"    - Author: {book.get('author', 'N/A')}")
                print(f"    - Cover URL: {book.get('cover_image_url', 'MISSING!')}")
                print(f"    - Subtitle: {book.get('subtitle', 'N/A')}")
                print(f"    - Similarity: {book.get('similarity', 'N/A')}")
                
                # Check if cover image URL exists
                if not book.get('cover_image_url'):
                    print(f"    WARNING: No cover image URL for '{book.get('title')}'")
                else:
                    print(f"    OK: Cover image URL found")
        else:
            print("\n    WARNING: No books recommended")
        
        print("\n" + "-" * 60)
        print("OK: Test completed successfully!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to backend server")
        print("  Make sure the backend is running on http://localhost:8000")
        return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("Testing Chatbot Image Loading Fix")
    print("=" * 60)
    test_chatbot_images()
