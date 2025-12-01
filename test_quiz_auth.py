#!/usr/bin/env python
"""
Test script to call the get-questions endpoint with token authentication
"""
import requests
import json

# The token from the browser logs
TOKEN = "ce4cf451-5149-420c-9eaa-141fec24dbd3"
LESSON_ID = 20
BASE_URL = "http://127.0.0.1:8000"

# Test without token (should fail with 302)
print("=" * 60)
print("TEST 1: Request WITHOUT token")
print("=" * 60)
response = requests.post(
    f"{BASE_URL}/api/courses/lessons/{LESSON_ID}/get-questions/",
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
)
print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Response length: {len(response.text)}")
if response.status_code == 302:
    print(f"Redirect to: {response.headers.get('Location')}")
print()

# Test with token (should succeed with 200)
print("=" * 60)
print("TEST 2: Request WITH token (Bearer)")
print("=" * 60)
response = requests.post(
    f"{BASE_URL}/api/courses/lessons/{LESSON_ID}/get-questions/",
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
    }
)
print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Response text length: {len(response.text)}")
try:
    data = response.json()
    print(f"Response JSON keys: {list(data.keys())}")
    if 'questions' in data:
        print(f"Got {len(data['questions'])} questions!")
        if data['questions']:
            print(f"First question: {data['questions'][0]}")
except:
    print("Response is not JSON (likely HTML login page)")
    print(f"First 200 chars: {response.text[:200]}")

print()
print("=" * 60)
print("TEST 3: Request WITH token (Token)")
print("=" * 60)
response = requests.post(
    f"{BASE_URL}/api/courses/lessons/{LESSON_ID}/get-questions/",
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Token {TOKEN}",
    }
)
print(f"Status: {response.status_code}")
try:
    data = response.json()
    print(f"Response JSON keys: {list(data.keys())}")
    if 'questions' in data:
        print(f"✅ Got {len(data['questions'])} questions!")
except:
    print("Response is not JSON")
    print(f"First 200 chars: {response.text[:200]}")
