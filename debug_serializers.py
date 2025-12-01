#!/usr/bin/env python
"""
Debug script to test serializers and understand validation errors
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from courses.serializers import CourseSerializer, CourseModuleSerializer
from rest_framework.serializers import ValidationError

print("=" * 60)
print("Testing CourseSerializer validation")
print("=" * 60)

# Test what happens with minimal data for Course
minimal_course_data = {
    'title': 'Test Course'
}

serializer = CourseSerializer(data=minimal_course_data)
print(f"Is valid with minimal data: {serializer.is_valid()}")
if not serializer.is_valid():
    print("Validation errors:")
    for field, errors in serializer.errors.items():
        print(f"  {field}: {errors}")
print()

# Test with more complete data
complete_course_data = {
    'title': 'Test Course',
    'slug': 'test-course',
    'short_description': 'A test course',
    'full_description': 'This is a test course',
    'price': 0,
    'level': 'Beginner',
    'category': 'Technology',
    'format': 'Online'
}

serializer = CourseSerializer(data=complete_course_data)
print(f"Is valid with complete data: {serializer.is_valid()}")
if not serializer.is_valid():
    print("Validation errors:")
    for field, errors in serializer.errors.items():
        print(f"  {field}: {errors}")
print()

print("=" * 60)
print("Testing CourseModuleSerializer validation")
print("=" * 60)

# Test what happens with minimal data for CourseModule
minimal_module_data = {
    'title': 'Module 1'
}

serializer = CourseModuleSerializer(data=minimal_module_data)
print(f"Is valid with minimal data: {serializer.is_valid()}")
if not serializer.is_valid():
    print("Validation errors:")
    for field, errors in serializer.errors.items():
        print(f"  {field}: {errors}")
print()

# Test with course_id
module_with_course_data = {
    'title': 'Module 1',
    'course': 1,
    'content': '{}',
    'order': 1
}

serializer = CourseModuleSerializer(data=module_with_course_data)
print(f"Is valid with course_id: {serializer.is_valid()}")
if not serializer.is_valid():
    print("Validation errors:")
    for field, errors in serializer.errors.items():
        print(f"  {field}: {errors}")
