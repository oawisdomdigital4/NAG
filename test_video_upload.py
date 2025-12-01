"""
Test script for video upload functionality in course curriculum
Tests both embedded links and direct video file uploads
"""

import os
import sys
import json
import requests
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

import django
django.setup()

from django.test import TestCase, Client
from courses.models import Course, CourseModule, Lesson
from accounts.models import User

API_BASE = 'http://127.0.0.1:8000'

def test_video_url_lesson():
    """Test creating a lesson with video URL (embedded link)"""
    print("\n" + "="*60)
    print("TEST 1: Create Lesson with Video URL (Embedded Link)")
    print("="*60)
    
    # Get or create facilitator
    facilitator, _ = User.objects.get_or_create(
        username='video_test_facilitator',
        defaults={'email': 'video_test@example.com', 'role': 'facilitator'}
    )
    
    # Create course
    course = Course.objects.create(
        title='Video Test Course',
        slug='video-test-course-' + str(Course.objects.count()),
        short_description='Testing video upload',
        full_description='Testing video upload functionality',
        facilitator=facilitator,
        price=0
    )
    
    # Create module
    module = CourseModule.objects.create(
        course=course,
        title='Test Module',
        content='{}',
        order=1
    )
    
    # Create lesson with video URL
    lesson = Lesson.objects.create(
        module=module,
        title='URL Embedded Video Lesson',
        lesson_type='video',
        description='This lesson has a video URL',
        video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        duration_minutes=10,
        order=1
    )
    
    print("[OK] Lesson created: {}".format(lesson.id))
    print("  Title: {}".format(lesson.title))
    print("  Video URL: {}".format(lesson.video_url))
    print("  Video File: {}".format(lesson.video_file or 'None'))
    print("  Duration: {} minutes".format(lesson.duration_minutes))
    
    # Test API response
    response = requests.get("{}/api/courses/lessons/{}/".format(API_BASE, lesson.id), headers={
        'Content-Type': 'application/json'
    })
    
    if response.status_code == 200:
        data = response.json()
        print("\n[OK] API Response:")
        print("  video_url: {}".format(data.get('video_url')))
        print("  video_file_url: {}".format(data.get('video_file_url')))
        print("  duration_minutes: {}".format(data.get('duration_minutes')))
        return True
    else:
        print("[ERROR] API Error: {} - {}".format(response.status_code, response.text))
        return False

def test_video_file_upload():
    """Test creating a lesson with uploaded video file"""
    print("\n" + "="*60)
    print("TEST 2: Create Lesson with Uploaded Video File")
    print("="*60)
    
    # Get or create facilitator
    facilitator, _ = User.objects.get_or_create(
        username='video_file_facilitator',
        defaults={'email': 'video_file@example.com', 'role': 'facilitator'}
    )
    
    # Create course
    course = Course.objects.create(
        title='Video File Test Course',
        slug='video-file-test-' + str(Course.objects.count()),
        short_description='Testing video file upload',
        full_description='Testing video file upload functionality',
        facilitator=facilitator,
        price=0
    )
    
    # Create module
    module = CourseModule.objects.create(
        course=course,
        title='Test Module',
        content='{}',
        order=1
    )
    
    # Create a dummy video file content (in production, this would be a real video)
    video_content = b'dummy video file content'
    video_file = SimpleUploadedFile(
        'test_video.mp4',
        video_content,
        content_type='video/mp4'
    )
    
    # Create lesson with video file
    lesson = Lesson.objects.create(
        module=module,
        title='Uploaded Video File Lesson',
        lesson_type='video',
        description='This lesson has an uploaded video file',
        video_file=video_file,
        duration_minutes=15,
        order=1
    )
    
    print(f"✓ Lesson created with video file: {lesson.id}")
    print(f"  Title: {lesson.title}")
    print(f"  Video URL: {lesson.video_url or 'None'}")
    print(f"  Video File: {lesson.video_file.name if lesson.video_file else 'None'}")
    print(f"  Video File URL: {lesson.video_file.url if lesson.video_file else 'None'}")
    print(f"  Duration: {lesson.duration_minutes} minutes")
    
    # Test API response
    response = requests.get(f"{API_BASE}/api/courses/lessons/{lesson.id}/", headers={
        'Content-Type': 'application/json'
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ API Response:")
        print(f"  video_url: {data.get('video_url')}")
        print(f"  video_file_url: {data.get('video_file_url')}")
        print(f"  duration_minutes: {data.get('duration_minutes')}")
        
        if data.get('video_file_url'):
            print(f"\n✓ Video file URL is available for streaming")
            return True
        else:
            print(f"\n✗ Video file URL not returned")
            return False
    else:
        print(f"✗ API Error: {response.status_code} - {response.text}")
        return False

def test_mixed_video_types():
    """Test module with mixed video types (some URLs, some files)"""
    print("\n" + "="*60)
    print("TEST 3: Module with Mixed Video Types")
    print("="*60)
    
    # Get or create facilitator
    facilitator, _ = User.objects.get_or_create(
        username='mixed_video_facilitator',
        defaults={'email': 'mixed_video@example.com', 'role': 'facilitator'}
    )
    
    # Create course
    course = Course.objects.create(
        title='Mixed Video Types Course',
        slug='mixed-video-test-' + str(Course.objects.count()),
        short_description='Testing mixed video types',
        full_description='Testing mixed video types in same module',
        facilitator=facilitator,
        price=0
    )
    
    # Create module
    module = CourseModule.objects.create(
        course=course,
        title='Mixed Videos Module',
        content='{}',
        order=1
    )
    
    # Lesson 1: Video URL
    lesson1 = Lesson.objects.create(
        module=module,
        title='YouTube Embedded Video',
        lesson_type='video',
        description='Embedded YouTube video',
        video_url='https://www.youtube.com/watch?v=abc123',
        duration_minutes=10,
        order=1
    )
    
    # Lesson 2: Uploaded video file
    video_file = SimpleUploadedFile(
        'course_video.mp4',
        b'video content here',
        content_type='video/mp4'
    )
    lesson2 = Lesson.objects.create(
        module=module,
        title='Uploaded Course Video',
        lesson_type='video',
        description='Uploaded MP4 video',
        video_file=video_file,
        duration_minutes=20,
        order=2
    )
    
    # Lesson 3: Quiz (non-video)
    lesson3 = Lesson.objects.create(
        module=module,
        title='Module Quiz',
        lesson_type='quiz',
        quiz_title='Chapter Review',
        passing_score=70,
        order=3
    )
    
    # Get module with all lessons
    response = requests.get(f"{API_BASE}/api/courses/course-modules/{module.id}/", headers={
        'Content-Type': 'application/json'
    })
    
    if response.status_code == 200:
        data = response.json()
        lessons = data.get('lessons', [])
        
        print(f"✓ Module fetched with {len(lessons)} lessons:")
        
        for i, lesson_data in enumerate(lessons, 1):
            print(f"\n  Lesson {i}: {lesson_data['title']}")
            print(f"    Type: {lesson_data['lesson_type']}")
            
            if lesson_data['lesson_type'] == 'video':
                print(f"    Video URL: {lesson_data.get('video_url') or 'None'}")
                print(f"    Video File URL: {lesson_data.get('video_file_url') or 'None'}")
                print(f"    Duration: {lesson_data.get('duration_minutes')} minutes")
        
        # Verify mixed types
        video_lessons = [l for l in lessons if l['lesson_type'] == 'video']
        quiz_lessons = [l for l in lessons if l['lesson_type'] == 'quiz']
        
        if len(video_lessons) == 2 and len(quiz_lessons) == 1:
            print(f"\n✓ Module correctly contains mixed lesson types")
            return True
        else:
            print(f"\n✗ Unexpected lesson mix: {len(video_lessons)} video, {len(quiz_lessons)} quiz")
            return False
    else:
        print(f"✗ API Error: {response.status_code} - {response.text}")
        return False

def main():
    print("\n" + "="*60)
    print("VIDEO UPLOAD FUNCTIONALITY TEST SUITE")
    print("="*60)
    
    try:
        # Wait for Django server
        print("\nWaiting for API to be ready...")
        for i in range(5):
            try:
                response = requests.get(f"{API_BASE}/api/", timeout=2)
                if response.status_code != 404:
                    break
            except:
                if i < 4:
                    import time
                    time.sleep(1)
        
        results = []
        
        # Run tests
        results.append(("Video URL Embedding", test_video_url_lesson()))
        results.append(("Video File Upload", test_video_file_upload()))
        results.append(("Mixed Video Types", test_mixed_video_types()))
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n✓ All tests passed! Video upload functionality is working.")
            return 0
        else:
            print(f"\n✗ {total - passed} test(s) failed.")
            return 1
            
    except Exception as e:
        print(f"\n✗ Test suite error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
