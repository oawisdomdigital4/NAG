#!/usr/bin/env python
"""
Test script to verify file integrity during upload and download
Ensures files are not mutated or modified by the system
"""

import os
import django
import hashlib
import tempfile
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from courses.models import Course, CourseModule, Lesson, Enrollment
from django.core.files.base import ContentFile

User = get_user_model()

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of file to verify integrity"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def test_file_integrity():
    """Test that files maintain integrity through upload and download"""
    print("\n" + "="*60)
    print("FILE INTEGRITY TEST")
    print("="*60)
    
    # Create test user and course
    print("\n[1] Setting up test data...")
    try:
        student = User.objects.create_user(
            username='student_test_integrity',
            email='student_integrity@test.com',
            password='testpass123'
        )
        facilitator = User.objects.create_user(
            username='facilitator_test_integrity',
            email='facilitator_integrity@test.com',
            password='testpass123',
            role='facilitator'
        )
        print(f"✓ Created test users: {student.username}, {facilitator.username}")
    except:
        student = User.objects.get(username='student_test_integrity')
        facilitator = User.objects.get(username='facilitator_test_integrity')
        print(f"✓ Using existing test users: {student.username}, {facilitator.username}")
    
    try:
        course = Course.objects.create(
            title="File Integrity Test Course",
            facilitator=facilitator,
            slug="file-integrity-test-course",
            status="published"
        )
        print(f"✓ Created course: {course.title}")
    except:
        course = Course.objects.get(slug="file-integrity-test-course")
        print(f"✓ Using existing course: {course.title}")
    
    try:
        module = CourseModule.objects.create(course=course, title="Test Module", order=1)
        lesson = Lesson.objects.create(
            module=module,
            title="File Integrity Test",
            lesson_type="assignment",
            order=1
        )
        print(f"✓ Created lesson: {lesson.title}")
    except:
        module = CourseModule.objects.get(course=course)
        lesson = Lesson.objects.get(module=module, lesson_type="assignment")
        print(f"✓ Using existing lesson: {lesson.title}")
    
    try:
        enrollment = Enrollment.objects.create(user=student, course=course)
        print(f"✓ Enrolled student in course")
    except:
        enrollment = Enrollment.objects.get(user=student, course=course)
        print(f"✓ Student already enrolled")
    
    # Create test files with known content
    print("\n[2] Creating test files with known content...")
    test_files = []
    
    # Test 1: Plain text file with special characters
    print("\n  Test File 1: Text with special characters")
    text_content = "Test content with special chars: ñ, é, ü, 中文, العربية, emoji: 😀🎉".encode('utf-8')
    text_hash = hashlib.sha256(text_content).hexdigest()
    print(f"    Content hash: {text_hash}")
    test_files.append(("test_text_special.txt", text_content, text_hash))
    
    # Test 2: Binary-like content (simulating Word doc)
    print("\n  Test File 2: Binary content (Word-like)")
    binary_content = b'\xff\xd8\xff\xe0' + os.urandom(1024) + b'\xff\xd9'  # JPEG-like header
    binary_hash = hashlib.sha256(binary_content).hexdigest()
    print(f"    Content hash: {binary_hash}")
    test_files.append(("test_binary.docx", binary_content, binary_hash))
    
    # Test 3: Real Word document marker
    print("\n  Test File 3: Office document structure")
    office_content = b'PK\x03\x04' + os.urandom(512)  # ZIP header (Word is ZIP)
    office_hash = hashlib.sha256(office_content).hexdigest()
    print(f"    Content hash: {office_hash}")
    test_files.append(("test_office.docx", office_content, office_hash))
    
    # Test upload and download cycle
    print("\n[3] Testing upload/download cycle for each file...")
    client = Client()
    
    for filename, file_content, original_hash in test_files:
        print(f"\n  Testing: {filename}")
        print(f"  Original size: {len(file_content)} bytes")
        print(f"  Original hash: {original_hash}")
        
        # Create temporary file for upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
        
        try:
            # Upload file via API
            with open(tmp_path, 'rb') as f:
                response = client.post(
                    f'/api/courses/lessons/{lesson.id}/submit-assignment/',
                    {
                        'content': 'Test assignment content for file integrity',
                        'attachments': f
                    },
                    HTTP_AUTHORIZATION=f'Bearer {student.auth_token.key}' if hasattr(student, 'auth_token') else None
                )
            
            print(f"  Upload status: {response.status_code}")
            
            if response.status_code == 201:
                # Get submission details to retrieve file URL
                data = response.json()
                if 'attachments' in data and len(data['attachments']) > 0:
                    attachment = data['attachments'][0]
                    file_url = attachment['url']
                    print(f"  Download URL: {file_url}")
                    
                    # Download file
                    download_response = client.get(file_url)
                    print(f"  Download status: {download_response.status_code}")
                    
                    if download_response.status_code == 200:
                        downloaded_content = download_response.content
                        downloaded_hash = hashlib.sha256(downloaded_content).hexdigest()
                        
                        print(f"  Downloaded size: {len(downloaded_content)} bytes")
                        print(f"  Downloaded hash: {downloaded_hash}")
                        
                        # Verify integrity
                        if downloaded_hash == original_hash:
                            print(f"  ✅ FILE INTEGRITY VERIFIED - Hash matches!")
                        else:
                            print(f"  ❌ FILE CORRUPTION DETECTED!")
                            print(f"    Expected: {original_hash}")
                            print(f"    Got:      {downloaded_hash}")
                            print(f"    Size diff: {len(file_content)} -> {len(downloaded_content)}")
                            
                            # Show first 100 bytes of each
                            print(f"    Original first 100 bytes: {file_content[:100]}")
                            print(f"    Downloaded first 100 bytes: {downloaded_content[:100]}")
                    else:
                        print(f"  ❌ DOWNLOAD FAILED: {download_response.status_code}")
                else:
                    print(f"  ❌ NO ATTACHMENTS IN RESPONSE")
            else:
                print(f"  ❌ UPLOAD FAILED: {response.status_code}")
                print(f"  Response: {response.json()}")
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    print("\n" + "="*60)
    print("FILE INTEGRITY TEST COMPLETE")
    print("="*60)

if __name__ == '__main__':
    test_file_integrity()
