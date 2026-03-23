#!/usr/bin/env python3
"""Debug profile update endpoint to see validation errors."""

import requests
import json

# Use a test token (this might fail auth, but we want to see the validation error)
TEST_TOKEN = "test-token"

endpoint = "http://localhost:8000/user-profile/me"

# Test 1: Send the exact payload the frontend would send
payload1 = {
    "display_name": "Test User",
    "profile_photo_url": None,
    "bio": None,
    "location": None,
    "favorite_genres_json": None,
}

print("=" * 60)
print("Test 1: With null values")
print("=" * 60)
print(f"Payload: {json.dumps(payload1, indent=2)}")

try:
    response = requests.patch(
        endpoint,
        json=payload1,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Send with empty strings
payload2 = {
    "display_name": "Test User",
    "profile_photo_url": "",
    "bio": "",
    "location": "",
    "favorite_genres_json": "",
}

print("\n" + "=" * 60)
print("Test 2: With empty strings")
print("=" * 60)
print(f"Payload: {json.dumps(payload2, indent=2)}")

try:
    response = requests.patch(
        endpoint,
        json=payload2,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Send with minimal payload
payload3 = {
    "display_name": "Test User",
}

print("\n" + "=" * 60)
print("Test 3: Minimal payload (only display_name)")
print("=" * 60)
print(f"Payload: {json.dumps(payload3, indent=2)}")

try:
    response = requests.patch(
        endpoint,
        json=payload3,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
