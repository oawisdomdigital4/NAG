#!/usr/bin/env python
"""Test thumbnail saving through API - using requests library"""
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
print("TESTING THUMBNAIL SAVE VIA API (Direct HTTP)")
print("=" * 80)

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

# Create test image bytes
print("\n[*] Creating test image...")
img = Image.new('RGB', (200, 200), color='blue')
img_io = BytesIO()
img.save(img_io, format='JPEG')
img_io.seek(0)
print(f"[+] Image created: 200x200 JPEG ({len(img_io.getvalue())} bytes)")

# Prepare request data
data = {
    'title': 'API Test Course Thumbnail',
    'slug': f'api-test-thumb-{os.urandom(3).hex()}',
    'category': 'Technology',
    'level': 'Beginner',
    'format': 'Online',
    'short_description': 'Test course with thumbnail',
    'full_description': 'This test course has a thumbnail image',
    'price': '49.99',
    'is_featured': 'false',
    'status': 'draft',
    'is_published': 'false',
}

# Prepare files
files = {
    'thumbnail': ('test_thumb.jpg', img_io, 'image/jpeg')
}

# Prepare headers
headers = {
    'Authorization': f'Bearer {str(token_obj.token)}'
}

# Send request
print("\n[*] Sending POST request to /api/courses/...")
url = 'http://127.0.0.1:8000/api/courses/'

try:
    response = requests.post(url, data=data, files=files, headers=headers)
    print(f"[+] Response Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n[SUCCESS] Course created!")
        print(f"  - ID: {result.get('id')}")
        print(f"  - Slug: {result.get('slug')}")
        print(f"  - Thumbnail field: {result.get('thumbnail')}")
        print(f"  - Thumbnail URL: {result.get('thumbnail_url_display') or result.get('thumbnail_url')}")
        
        # Verify in database
        course = Course.objects.get(id=result.get('id'))
        print(f"\n[DB VERIFICATION]")
        print(f"  - Thumbnail DB field: {course.thumbnail}")
        print(f"  - Thumbnail URL: {course.thumbnail.url if course.thumbnail else 'NONE'}")
        
        if course.thumbnail:
            print(f"  - File path: {course.thumbnail.path}")
            import os
            if os.path.exists(course.thumbnail.path):
                size = os.path.getsize(course.thumbnail.path)
                print(f"  [+] File exists on disk ({size} bytes)")
            else:
                print(f"  [-] File NOT found on disk!")
                print(f"      Expected at: {course.thumbnail.path}")
        else:
            print(f"  [-] No thumbnail saved in database!")
    else:
        print(f"[ERROR] Response Status: {response.status_code}")
        try:
            result = response.json()
            print(f"  Error details: {json.dumps(result, indent=2)}")
        except:
            print(f"  Response body: {response.text}")
            
except Exception as e:
    print(f"[ERROR] Request failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
