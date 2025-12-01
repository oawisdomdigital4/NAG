#!/usr/bin/env python
"""Test course update to see what's causing the 400 error"""
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
print("TESTING COURSE UPDATE - DEBUGGING 400 ERROR")
print("=" * 80)

# Get existing course
course = Course.objects.filter(slug='introduction-to-web-development').first()
if not course:
    print("[-] Course not found!")
    exit(1)

print(f"[+] Found course: {course.title} (ID: {course.id})")

# Create a test user/facilitator if not exists
User = get_user_model()
user = User.objects.filter(username='testfacilitator').first()
if not user:
    user = User.objects.create_user(
        username='testfacilitator',
        email='testfacilitator@example.com',
        password='testpass123',
        role='facilitator'
    )
    print(f"[+] Created test user: {user.username}")
else:
    print(f"[+] Using existing user: {user.username}")

# Get auth token
token_obj = UserToken.objects.filter(user=user).first()
if not token_obj:
    import uuid
    token_obj = UserToken.objects.create(
        user=user,
        token=str(uuid.uuid4()),
        expires_at=datetime.now() + timedelta(days=30)
    )
    print(f"[+] Created new token")
else:
    print(f"[+] Using existing token")

# Prepare update data
data = {
    'title': 'Introduction to Web Development - Updated',
    'category': 'Technology',
    'level': 'Beginner',
    'format': 'Online',
    'short_description': 'Updated description',
    'full_description': 'Updated full description',
    'price': '99.99',
}

# Prepare headers
headers = {
    'Authorization': f'Bearer {str(token_obj.token)}'
}

# Send request
print("\n[*] Sending PUT request to update course...")
url = f'http://127.0.0.1:8000/api/courses/{course.slug}/'

try:
    response = requests.put(url, json=data, headers=headers)
    print(f"[+] Response Status: {response.status_code}")
    
    result = response.json()
    print(f"\n[RESPONSE]")
    print(json.dumps(result, indent=2))
    
    if response.status_code not in [200, 201]:
        print(f"\n[-] ERROR - Status {response.status_code}")
        
except Exception as e:
    print(f"[-] Request failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
