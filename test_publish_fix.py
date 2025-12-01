#!/usr/bin/env python
"""Test the fixed publish logic (simulating the frontend fix)"""
import os
import sys
import django

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course
from accounts.models import UserToken
from datetime import datetime, timedelta
import requests
import json

print("=" * 80)
print("TEST: FRONTEND PUBLISH FIX")
print("=" * 80)

# Create test user
User = get_user_model()
user = User.objects.filter(username='testfacilitator').first()
if not user:
    user = User.objects.create_user(
        username='testfacilitator',
        email='testfacilitator@example.com',
        password='testpass123',
        role='facilitator'
    )

# Get token
token_obj = UserToken.objects.filter(user=user).first()
if not token_obj:
    import uuid
    token_obj = UserToken.objects.create(
        user=user,
        token=str(uuid.uuid4()),
        expires_at=datetime.now() + timedelta(days=30)
    )

# Create a new course
course = Course.objects.create(
    title='Test Publish Flow',
    slug=f'test-publish-flow-{os.urandom(3).hex()}',
    short_description='Test publishing workflow',
    full_description='Testing the complete publish workflow',
    facilitator=user,
    price=79.99,
    status='draft',
    is_published=False,
    category='Technology',
    level='Beginner',
    format='Online'
)
print(f"[+] Created test course: {course.slug}")
print(f"    Initial status: {course.status}")
print(f"    Initial is_published: {course.is_published}")

# Simulate the fixed frontend logic
print(f"\n[*] STEP 1: GET current course data...")
response = requests.get(
    f'http://127.0.0.1:8000/api/courses/{course.slug}/',
    headers={'Authorization': f'Bearer {token_obj.token}'}
)

if response.status_code != 200:
    print(f"[-] Failed: {response.status_code}")
    exit(1)

currentRes = response.json()
print(f"[+] Got current data")

# Simulate the FIXED publishCourse function
print(f"\n[*] STEP 2: Build clean payload (FIXED approach)...")
payload = {
    'title': currentRes.get('title'),
    'slug': currentRes.get('slug'),
    'short_description': currentRes.get('short_description'),
    'full_description': currentRes.get('full_description'),
    'price': currentRes.get('price'),
    'duration': currentRes.get('duration'),
    'category': currentRes.get('category'),
    'level': currentRes.get('level'),
    'format': currentRes.get('format'),
    'is_featured': currentRes.get('is_featured'),
    'status': 'published',
    'is_published': True,
}
print(f"[+] Payload keys: {list(payload.keys())}")

# Send the publish request
print(f"\n[*] STEP 3: Send PUT request with CLEAN payload...")
response = requests.put(
    f'http://127.0.0.1:8000/api/courses/{course.slug}/',
    json=payload,
    headers={'Authorization': f'Bearer {token_obj.token}'}
)

print(f"[+] Response Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"[SUCCESS] Course published!")
    print(f"    New status: {result.get('status')}")
    print(f"    New is_published: {result.get('is_published')}")
    
    # Verify in database
    course.refresh_from_db()
    print(f"\n[DB VERIFICATION]")
    print(f"    DB status: {course.status}")
    print(f"    DB is_published: {course.is_published}")
else:
    print(f"[-] Failed with {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

print("\n" + "=" * 80)
