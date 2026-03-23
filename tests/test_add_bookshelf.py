#!/usr/bin/env python3
"""Debug add to bookshelf endpoint."""

import requests
import json

# Test token - this will fail auth but we want to see validation errors
TEST_TOKEN = "test-token"
TEST_USER_ID = "test-user-123"

# Pick a random book ID from the database (or use a test one)
TEST_BOOK_ID = "6462"  # From earlier chatbot test

endpoint = "http://localhost:8000/bookshelf/"

# Test payload
payload = {
    "book_id": TEST_BOOK_ID,
}

print("=" * 60)
print("Testing: Add Book to Bookshelf")
print("=" * 60)
print(f"Endpoint: {endpoint}")
print(f"Book ID: {TEST_BOOK_ID}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("-" * 60)

try:
    response = requests.post(
        endpoint,
        json=payload,
        headers={
            "Authorization": f"Bearer {TEST_TOKEN}",
            "Content-Type": "application/json",
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\nSUCCESS!")
        print(json.dumps(response.json(), indent=2))
    else:
        print("\nERROR:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
            
except Exception as e:
    print(f"Request Error: {e}")
