#!/usr/bin/env python
"""Test course update with multipart form data - like the frontend does"""
import os
import sys
import django
from io import BytesIO
from PIL import Image

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
print("TESTING COURSE UPDATE WITH MULTIPART - DEBUGGING 400 ERROR")
print("=" * 80)

# Get existing course or create a test one
User = get_user_model()
test_user = User.objects.filter(username='testfacilitator').first()
if not test_user:
    test_user = User.objects.create_user(
        username='testfacilitator',
        email='testfacilitator@example.com',
        password='testpass123',
        role='facilitator'
    )

course = Course.objects.filter(facilitator=test_user).first()
if not course:
    print("[-] No course found for test user. Creating one...")
    course = Course.objects.create(
        title='Test Update Course',
        slug=f'test-update-{os.urandom(3).hex()}',
        short_description='Test',
        full_description='Test course',
        facilitator=test_user,
        price=49.99
    )
    print(f"[+] Created test course: {course.title}")
else:
    print(f"[+] Found course: {course.title} (ID: {course.id})")

# Get auth token
token_obj = UserToken.objects.filter(user=test_user).first()
if not token_obj:
    import uuid
    token_obj = UserToken.objects.create(
        user=test_user,
        token=str(uuid.uuid4()),
        expires_at=datetime.now() + timedelta(days=30)
    )

print(f"[+] Using course: {course.slug}")

# Prepare update data - multipart form data
data = {
    'title': 'Test Update Course - Modified',
    'slug': course.slug,
    'category': 'Technology',
    'level': 'Beginner',
    'format': 'Online',
    'short_description': 'Updated description',
    'full_description': 'Updated full description',
    'price': '99.99',
    'duration': '10 hours',
}

# Prepare headers
headers = {
    'Authorization': f'Bearer {str(token_obj.token)}'
}

# Send request
print("\n[*] Sending PUT request with multipart form data...")
url = f'http://127.0.0.1:8000/api/courses/{course.slug}/'

try:
    response = requests.put(url, data=data, headers=headers)
    print(f"[+] Response Status: {response.status_code}")
    
    try:
        result = response.json()
        print(f"\n[RESPONSE]")
        print(json.dumps(result, indent=2))
    except:
        print(f"Response text: {response.text}")
    
    if response.status_code not in [200, 201]:
        print(f"\n[-] ERROR - Status {response.status_code}")
        
except Exception as e:
    print(f"[-] Request failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
