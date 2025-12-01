#!/usr/bin/env python
"""Debug the exact 400 error message when publishing"""
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
print("DEBUG: EXACT 400 ERROR FROM PUBLISH")
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

# Get an existing course or create one
course = Course.objects.filter(facilitator=user).first()
if not course:
    course = Course.objects.create(
        title='Test Publish Course',
        slug=f'test-publish-{os.urandom(3).hex()}',
        short_description='Test',
        full_description='Test course',
        facilitator=user,
        price=49.99,
        status='draft',
        is_published=False
    )
    print(f"[+] Created test course: {course.slug}")
else:
    print(f"[+] Found course: {course.slug}")

# First, GET the course to see what fields are returned
print("\n[*] GETting course to see all response fields...")
response = requests.get(
    f'http://127.0.0.1:8000/api/courses/{course.slug}/',
    headers={'Authorization': f'Bearer {token_obj.token}'}
)
print(f"GET Status: {response.status_code}")

if response.status_code == 200:
    current_data = response.json()
    print(f"\n[*] Response keys: {list(current_data.keys())}")
    
    # Show problematic fields
    print(f"\n[*] Response field details:")
    print(f"    - modules: {type(current_data.get('modules'))} with {len(current_data.get('modules', []))} items")
    print(f"    - reviews: {type(current_data.get('reviews'))} with {len(current_data.get('reviews', []))} items")
    print(f"    - enrollments_count: {current_data.get('enrollments_count')}")
    print(f"    - status: {current_data.get('status')}")
    print(f"    - is_published: {current_data.get('is_published')}")
    
    # Try publishing with all fields (like the frontend does)
    print(f"\n[*] Attempting publish with ALL response fields...")
    publish_data = current_data.copy()
    publish_data['status'] = 'published'
    publish_data['is_published'] = True
    # Remove the meta fields
    publish_data.pop('_status', None)
    publish_data.pop('_ok', None)
    
    response2 = requests.put(
        f'http://127.0.0.1:8000/api/courses/{course.slug}/',
        json=publish_data,
        headers={'Authorization': f'Bearer {token_obj.token}'}
    )
    print(f"PUT Status: {response2.status_code}")
    
    if response2.status_code != 200:
        print(f"\n[-] ERROR RESPONSE:")
        print(json.dumps(response2.json(), indent=2))
    else:
        print(f"[+] SUCCESS!")
        
    # Now try with cleaned fields (as fix)
    print(f"\n[*] Attempting publish with CLEAN fields only...")
    clean_data = {
        'title': current_data.get('title'),
        'slug': current_data.get('slug'),
        'category': current_data.get('category'),
        'level': current_data.get('level'),
        'format': current_data.get('format'),
        'duration': current_data.get('duration'),
        'short_description': current_data.get('short_description'),
        'full_description': current_data.get('full_description'),
        'price': current_data.get('price'),
        'is_featured': current_data.get('is_featured'),
        'status': 'published',
        'is_published': True,
    }
    
    response3 = requests.put(
        f'http://127.0.0.1:8000/api/courses/{course.slug}/',
        json=clean_data,
        headers={'Authorization': f'Bearer {token_obj.token}'}
    )
    print(f"PUT Status: {response3.status_code}")
    
    if response3.status_code != 200:
        print(f"\n[-] ERROR RESPONSE:")
        print(json.dumps(response3.json(), indent=2))
    else:
        print(f"[+] SUCCESS with cleaned fields!")

print("\n" + "=" * 80)
