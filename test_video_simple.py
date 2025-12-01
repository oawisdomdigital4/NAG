#!/usr/bin/env python
"""Simple test for video upload functionality"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import Course, CourseModule, Lesson
from accounts.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

print("TEST: Video Upload Functionality")
print("=" * 60)

# Create facilitator
facilitator, created = User.objects.get_or_create(
    username='video_test_fac_v2',
    defaults={'email': 'video_test_v2@example.com', 'role': 'facilitator'}
)
print("[1] Facilitator: {} (created={})".format(facilitator.username, created))

# Create course
course = Course.objects.create(
    title='Video Test Course V2',
    slug='video-test-v2-' + str(Course.objects.count()),
    short_description='Testing video',
    full_description='Testing video upload',
    facilitator=facilitator,
    price=0
)
print("[2] Course created: ID {} - {}".format(course.id, course.title))

# Create module
module = CourseModule.objects.create(
    course=course,
    title='Test Module',
    content='{}',
    order=1
)
print("[3] Module created: ID {} - {}".format(module.id, module.title))

# Test 1: Create lesson with video URL
lesson1 = Lesson.objects.create(
    module=module,
    title='URL Video Lesson',
    lesson_type='video',
    description='Test URL video',
    video_url='https://www.youtube.com/watch?v=test123',
    duration_minutes=10,
    order=1
)
print("[4] Lesson 1 (URL) created: ID {}".format(lesson1.id))
print("    - video_url: {}".format(lesson1.video_url))
print("    - video_file: {}".format(lesson1.video_file or 'None'))
print("    - duration: {} min".format(lesson1.duration_minutes))

# Test 2: Create lesson with video file
video_file = SimpleUploadedFile(
    'test_video.mp4',
    b'dummy video content for testing',
    content_type='video/mp4'
)
lesson2 = Lesson.objects.create(
    module=module,
    title='Uploaded Video Lesson',
    lesson_type='video',
    description='Test uploaded video',
    video_file=video_file,
    duration_minutes=15,
    order=2
)
print("[5] Lesson 2 (FILE) created: ID {}".format(lesson2.id))
print("    - video_url: {}".format(lesson2.video_url or 'None'))
print("    - video_file: {}".format(lesson2.video_file.name if lesson2.video_file else 'None'))
print("    - video_file_url: {}".format(lesson2.video_file.url if lesson2.video_file else 'None'))
print("    - duration: {} min".format(lesson2.duration_minutes))

# Test 3: Verify both are in the same module
lessons = module.lessons.all().order_by('order')
print("[6] Module lessons count: {}".format(lessons.count()))
for idx, l in enumerate(lessons, 1):
    print("    - Lesson {}: {} ({})".format(idx, l.title, l.lesson_type))

print()
print("SUCCESS: All tests completed")
print("=" * 60)
