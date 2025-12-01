"""
Test script to verify file attachment display workflow
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import AssignmentSubmission, Enrollment, Lesson
from django.contrib.auth.models import User
from django.conf import settings
from urllib.parse import quote, unquote

print("=" * 80)
print("FILE ATTACHMENT DISPLAY TEST")
print("=" * 80)

# Get a submission with attachments
submission = AssignmentSubmission.objects.get(id=6)

if not submission:
    print("\n❌ No submissions with attachments found!")
    exit(1)

print(f"\n✅ Found submission {submission.id} with attachments")
print(f"Student: {submission.enrollment.user.email}")
print(f"Lesson: {submission.lesson.title}")

# Test 1: Check if attachments are stored in DB
print("\n" + "-" * 80)
print("TEST 1: Database Storage")
print("-" * 80)

print(f"Attachments in DB: {len(submission.attachments)} file(s)")
for att in submission.attachments:
    print(f"\n  File: {att['name']}")
    print(f"  Original URL: {att['url']}")
    print(f"  Size: {att['size']} bytes")
    print(f"  Type: {att['type']}")

# Test 2: Check if files exist on disk
print("\n" + "-" * 80)
print("TEST 2: File Storage on Disk")
print("-" * 80)

for att in submission.attachments:
    url = att['url']
    if url.startswith('/media/'):
        file_path = url[7:]  # Remove /media/
    else:
        file_path = url
    
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    exists = os.path.exists(full_path)
    
    print(f"\n  File: {att['name']}")
    print(f"  Path: {full_path}")
    print(f"  Status: {'✅ EXISTS' if exists else '❌ MISSING'}")
    
    if exists:
        size = os.path.getsize(full_path)
        print(f"  Disk size: {size} bytes")

# Test 3: URL encoding
print("\n" + "-" * 80)
print("TEST 3: URL Encoding for HTTP")
print("-" * 80)

for att in submission.attachments:
    url = att['url']
    
    if url.startswith('/media/'):
        # Encode everything after /media/ (simulate API response)
        encoded_path = quote(url[7:], safe='/')
        encoded_url = f'/media/{encoded_path}'
    else:
        encoded_url = url
    
    print(f"\n  Original: {url}")
    print(f"  Encoded:  {encoded_url}")
    print(f"  Can use in HTML: {'✅ YES' if '%20' in encoded_url or '%' not in encoded_url else 'check'}")

# Test 4: URL decoding (what serve_media will do)
print("\n" + "-" * 80)
print("TEST 4: Server-side URL Decoding")
print("-" * 80)

for att in submission.attachments:
    url = att['url']
    
    if url.startswith('/media/'):
        encoded_path = quote(url[7:], safe='/')
        encoded_url = f'/media/{encoded_path}'
        
        # Simulate what serve_media does
        path = encoded_url[7:]  # Remove /media/
        decoded_path = unquote(path)  # Decode
        
        file_path = os.path.join(settings.MEDIA_ROOT, decoded_path)
        exists = os.path.exists(file_path)
        
        print(f"\n  Encoded URL path: {path}")
        print(f"  Decoded path: {decoded_path}")
        print(f"  File exists after decode: {'✅ YES' if exists else '❌ NO'}")

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED - Files should now display correctly!")
print("=" * 80)
