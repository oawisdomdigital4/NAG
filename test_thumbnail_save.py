#!/usr/bin/env python
"""Test thumbnail saving through API"""
import os
import sys
import django

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
import json

print("=" * 80)
print("TESTING THUMBNAIL SAVE VIA API")
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
    print(f"✓ Created test user: {user.username}")
else:
    print(f"✓ Using existing user: {user.username}")

# Get auth token
from accounts.models import UserToken
from datetime import datetime, timedelta
token_obj = UserToken.objects.filter(user=user).first()
if not token_obj:
    # Generate a new token
    import uuid
    token_obj = UserToken.objects.create(
        user=user,
        token=str(uuid.uuid4()),
        expires_at=datetime.now() + timedelta(days=30)
    )
    print(f"✓ Created new token: {str(token_obj.token)[:20]}...")
else:
    print(f"✓ Using existing token: {str(token_obj.token)[:20]}...")

# Create test client
client = Client()

# Create a test image
print("\nCreating test image...")
img = Image.new('RGB', (200, 200), color='blue')
img_io = BytesIO()
img.save(img_io, format='JPEG')
img_io.seek(0)

# Prepare multipart form data
from django.test.client import encode_multipart, BOUNDARY

data = {
    'title': 'API Test Course',
    'slug': f'api-test-{os.urandom(3).hex()}',
    'category': 'Technology',
    'level': 'Beginner',
    'format': 'Online',
    'short_description': 'Test course from API',
    'full_description': 'This is a test course created via API with thumbnail',
    'price': '49.99',
    'is_featured': 'false',
    'status': 'draft',
    'is_published': 'false',
}

# Recreate BytesIO for upload
img_io = BytesIO()
img = Image.new('RGB', (200, 200), color='blue')
img.save(img_io, format='JPEG')
img_io.seek(0)

print("\nTesting Course Creation with Thumbnail via API...")
print(f"  - Title: {data['title']}")
print(f"  - Slug: {data['slug']}")
print(f"  - Image: 200x200 JPEG")

# Test with file
img_io_for_upload = BytesIO()
img = Image.new('RGB', (200, 200), color='blue')
img.save(img_io_for_upload, format='JPEG')
img_io_for_upload.seek(0)

# Use client.post with FILES
response = client.post(
    '/api/courses/',
    data=data,
    files={'thumbnail': SimpleUploadedFile('test.jpg', img_io_for_upload.getvalue(), content_type='image/jpeg')},
    HTTP_AUTHORIZATION=f'Bearer {token_obj.token}',
    content_type='multipart/form-data',
)

print(f"\nResponse Status: {response.status_code}")
if response.status_code in [200, 201]:
    try:
        result = json.loads(response.content)
        print(f"✓ Course created successfully!")
        print(f"  - ID: {result.get('id')}")
        print(f"  - Slug: {result.get('slug')}")
        print(f"  - Thumbnail field: {result.get('thumbnail')}")
        print(f"  - Thumbnail URL: {result.get('thumbnail_url_display') or result.get('thumbnail_url')}")
        
        # Verify in database
        from courses.models import Course
        course = Course.objects.get(id=result.get('id'))
        print(f"\n✓ Verified in database:")
        print(f"  - Thumbnail DB field: {course.thumbnail}")
        print(f"  - Thumbnail URL: {course.thumbnail.url if course.thumbnail else 'NONE'}")
        
        if course.thumbnail:
            print(f"  - File path: {course.thumbnail.path}")
            if os.path.exists(course.thumbnail.path):
                size = os.path.getsize(course.thumbnail.path)
                print(f"  ✓ File exists on disk ({size} bytes)")
            else:
                print(f"  ✗ File NOT found on disk")
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response: {response.content}")
else:
    print(f"✗ Error: {response.status_code}")
    print(f"Response: {response.content}")

print("\n" + "=" * 80)
