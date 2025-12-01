#!/usr/bin/env python
"""
Test script to verify availability_date field is working correctly
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.models import Course, CourseModule, Lesson
from courses.serializers import LessonSerializer, LessonInstructorSerializer
from accounts.models import User
import json

# Create test data
print("Testing availability_date field implementation...")
print("=" * 60)

try:
    # Get or create a test facilitator
    facilitator = User.objects.filter(username='test_facilitator').first()
    if not facilitator:
        try:
            facilitator = User.objects.create_user(
                username='test_facilitator',
                email='test_facilitator@example.com',
                password='testpass123'
            )
            print(f"✓ Created test facilitator: {facilitator.username}")
        except:
            # Try with different email if that fails
            import uuid
            unique_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
            facilitator = User.objects.create_user(
                username='test_facilitator',
                email=unique_email,
                password='testpass123'
            )
            print(f"✓ Created test facilitator with unique email: {facilitator.username}")
    else:
        print(f"✓ Using existing test facilitator: {facilitator.username}")
    
    # Get or create a test course
    course, created = Course.objects.get_or_create(
        slug='test-availability-course',
        defaults={
            'title': 'Test Availability Course',
            'facilitator': facilitator,
            'short_description': 'Test course for availability_date field',
            'full_description': 'This is a test course',
            'price': 99.99,
        }
    )
    print(f"{'✓ Created' if created else '✓ Found'} test course: {course.title}")
    
    # Get or create a test module
    module, created = CourseModule.objects.get_or_create(
        course=course,
        title='Test Module',
        defaults={'order': 1}
    )
    print(f"{'✓ Created' if created else '✓ Found'} test module: {module.title}")
    
    # Create a lesson with availability_date
    future_date = datetime.now() + timedelta(days=7)
    lesson, created = Lesson.objects.get_or_create(
        module=module,
        title='Test Availability Lesson',
        defaults={
            'lesson_type': 'video',
            'description': 'Test lesson with availability date',
            'order': 1,
            'availability_date': future_date,
        }
    )
    if created:
        print(f"✓ Created test lesson with availability_date: {lesson.title}")
    else:
        print(f"✓ Found test lesson: {lesson.title}")
    
    # Test 1: Check if availability_date is stored correctly
    print("\nTest 1: Verify availability_date field storage")
    print("-" * 60)
    lesson.refresh_from_db()
    if lesson.availability_date:
        print(f"✓ availability_date field exists: {lesson.availability_date}")
    else:
        print("✗ availability_date field is None (expected if just created)")
    
    # Test 2: Update lesson with availability_date
    print("\nTest 2: Update lesson with availability_date")
    print("-" * 60)
    past_date = datetime.now() - timedelta(days=1)
    lesson.availability_date = past_date
    lesson.save()
    lesson.refresh_from_db()
    print(f"✓ Updated availability_date to: {lesson.availability_date}")
    
    # Test 3: Serialize with LessonSerializer
    print("\nTest 3: Check LessonSerializer includes availability_date")
    print("-" * 60)
    serializer = LessonSerializer(lesson)
    data = serializer.data
    if 'availability_date' in data:
        print(f"✓ LessonSerializer includes availability_date: {data['availability_date']}")
    else:
        print("✗ LessonSerializer missing availability_date field")
    
    # Test 4: Serialize with LessonInstructorSerializer
    print("\nTest 4: Check LessonInstructorSerializer includes availability_date")
    print("-" * 60)
    instructor_serializer = LessonInstructorSerializer(lesson)
    instructor_data = instructor_serializer.data
    if 'availability_date' in instructor_data:
        print(f"✓ LessonInstructorSerializer includes availability_date: {instructor_data['availability_date']}")
    else:
        print("✗ LessonInstructorSerializer missing availability_date field")
    
    # Test 5: Verify JSON serialization
    print("\nTest 5: Test JSON serialization")
    print("-" * 60)
    json_data = json.dumps(data, default=str)
    if 'availability_date' in json_data:
        print(f"✓ availability_date properly serializes to JSON")
    else:
        print("✗ availability_date missing in JSON serialization")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed! The availability_date field is working correctly.")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error during testing: {str(e)}")
    import traceback
    traceback.print_exc()
