#!/usr/bin/env python3
"""
End-to-end test script for thumbnail upload.
This script:
1. Creates a test user with proper authentication
2. Generates a valid token
3. Creates a test image file
4. Provides curl command to test the upload
5. Verifies the file was saved to database and filesystem
"""
import os
import sys
import django
from pathlib import Path
from PIL import Image
from io import BytesIO
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserToken
from courses.models import Course
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def create_test_image_file():
    """Create a test image file on disk."""
    test_image_path = Path(__file__).parent / 'test_thumbnail.jpg'
    
    # Create a colorful test image
    img = Image.new('RGB', (1280, 720), color=(70, 150, 200))
    img.save(test_image_path, 'JPEG')
    
    print(f"✓ Created test image: {test_image_path}")
    return test_image_path

def setup_test_user():
    """Create a test user and get their token."""
    # Clean up existing test user
    User.objects.filter(username='curl_test_user').delete()
    
    # Create new user
    user = User.objects.create_user(
        username='curl_test_user',
        email='curl_test@example.com',
        password='testpass123',
        role='facilitator',
        first_name='Curl',
        last_name='Tester'
    )
    
    # Create token
    token_obj = UserToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(days=7)
    )
    
    print(f"✓ Created test user: curl_test_user")
    print(f"✓ User ID: {user.id}")
    print(f"✓ Token: {token_obj.token}")
    
    return user, token_obj

def main():
    print("=" * 80)
    print("END-TO-END THUMBNAIL UPLOAD TEST")
    print("=" * 80)
    
    # Create test image
    print("\n[Step 1] Creating test image...")
    test_image_path = create_test_image_file()
    
    # Create test user and token
    print("\n[Step 2] Creating test user and authentication token...")
    user, token_obj = setup_test_user()
    
    # Generate test slug
    test_slug = f"e2e-test-{str(uuid.uuid4())[:8]}"
    
    print("\n" + "=" * 80)
    print("CURL COMMAND TO TEST THUMBNAIL UPLOAD")
    print("=" * 80)
    
    curl_command = f"""curl -X POST \\
  -H "Authorization: Bearer {token_obj.token}" \\
  -H "Accept: application/json" \\
  -F "title=E2E Test Course" \\
  -F "slug={test_slug}" \\
  -F "category=Technology" \\
  -F "level=Beginner" \\
  -F "format=Self-paced" \\
  -F "duration=10 hours" \\
  -F "short_description=Test course from curl" \\
  -F "full_description=This is an end-to-end test of the thumbnail upload system" \\
  -F "price=99.99" \\
  -F "is_featured=false" \\
  -F "status=draft" \\
  -F "is_published=false" \\
  -F "thumbnail=@{test_image_path}" \\
  http://127.0.0.1:8000/api/courses/courses/
"""
    
    print("\n✓ Copy and paste this command into your terminal:\n")
    print(curl_command)
    
    print("\n" + "=" * 80)
    print("EXPECTED RESPONSE (on success):")
    print("=" * 80)
    print("""
HTTP/1.1 201 Created

{
  "id": <course_id>,
  "title": "E2E Test Course",
  "slug": "e2e-test-...",
  "thumbnail_url": "/media/course_thumbnails/...",
  "thumbnail": "http://127.0.0.1:8000/media/course_thumbnails/...",
  ...other fields...
}
""")
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMMAND (after upload):")
    print("=" * 80)
    print(f"""
python manage.py shell << 'EOF'
from courses.models import Course

course = Course.objects.get(slug='{test_slug}')
print(f"Course ID: {{course.id}}")
print(f"Thumbnail field: {{course.thumbnail}}")
print(f"Thumbnail URL: {{course.thumbnail.url if course.thumbnail else 'None'}}")
print(f"File path: {{course.thumbnail.path if course.thumbnail else 'None'}}")

# Verify file exists on disk
import os
if course.thumbnail and os.path.exists(course.thumbnail.path):
    print("✓ File exists on disk")
    print(f"  Path: {{course.thumbnail.path}}")
    print(f"  Size: {{os.path.getsize(course.thumbnail.path)}} bytes")
else:
    print("✗ File not found on disk")
EOF
""")
    
    print("\n" + "=" * 80)
    print("CLEANUP COMMAND (after testing):")
    print("=" * 80)
    print(f"""
python manage.py shell << 'EOF'
from courses.models import Course
from django.contrib.auth import get_user_model

# Delete test course
Course.objects.filter(slug='{test_slug}').delete()
print("✓ Test course deleted")

# Delete test user
User = get_user_model()
User.objects.filter(username='curl_test_user').delete()
print("✓ Test user deleted")
EOF
""")
    
    print("\n" + "=" * 80)
    print("TROUBLESHOOTING:")
    print("=" * 80)
    print("""
If you get "401 Unauthorized":
  → Token might be expired or invalid
  → Check the token value matches exactly
  → Regenerate with this script

If you get "400 Bad Request":
  → Check all required fields are included
  → Check slug format (lowercase, no spaces, max 50 chars)
  → Check price is a number

If you get "415 Unsupported Media Type":
  → Backend parser configuration issue
  → Run: python manage.py shell
  → from courses.views import CourseViewSet
  → print(CourseViewSet().get_parsers())

If file uploads but doesn't appear in database:
  → Check the serializer is returning thumbnail_url
  → Run the verification command above

File not appearing in /media/course_thumbnails/:
  → Check MEDIA_ROOT in settings.py
  → Check file permissions
  → Check if the file field is being saved to database
""")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
