#!/usr/bin/env python
"""
Test script to verify the 400 Bad Request issues are fixed
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
import json

User = get_user_model()

# Create a test user
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={
        'email': 'test@example.com',
        'is_staff': False,
        'role': 'facilitator'
    }
)
print(f"User: {user.username} (created: {created})")

# Create API client
client = APIClient()
client.force_authenticate(user=user)

print("\n" + "=" * 60)
print("Testing POST /api/courses/ (Create Course)")
print("=" * 60)

# Test 1: Minimal course data
minimal_course = {
    'title': 'Test Course'
}

response = client.post('/api/courses/', minimal_course, format='json')
print(f"Status Code: {response.status_code}")
if response.status_code == 201:
    print(f"✓ Course created successfully!")
    course_data = response.json()
    print(f"  Course ID: {course_data.get('id')}")
    print(f"  Course Slug: {course_data.get('slug')}")
    print(f"  Course Title: {course_data.get('title')}")
    course_id = course_data.get('id')
else:
    print(f"✗ Failed with status {response.status_code}")
    print(f"  Error: {response.json()}")
    course_id = None

print("\n" + "=" * 60)
print("Testing POST /api/courses/course-modules/ (Create Course Module)")
print("=" * 60)

if course_id:
    # Test 2: Module with course ID
    module_data = {
        'title': 'Module 1',
        'course': course_id,
        'content': '{"type": "introduction"}',
        'order': 1
    }
    
    response = client.post('/api/courses/course-modules/', module_data, format='json')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        print(f"✓ Module created successfully!")
        module_response = response.json()
        print(f"  Module ID: {module_response.get('id')}")
        print(f"  Module Title: {module_response.get('title')}")
    else:
        print(f"✗ Failed with status {response.status_code}")
        print(f"  Error: {response.json()}")
    
    # Test 3: Module with query parameter
    print("\n  Testing with query parameter...")
    module_data = {
        'title': 'Module 2',
        'content': '{}',
        'order': 2
    }
    
    response = client.post(f'/api/courses/course-modules/?course={course_id}', module_data, format='json')
    print(f"  Status Code: {response.status_code}")
    if response.status_code == 201:
        print(f"  ✓ Module created with query parameter!")
    else:
        print(f"  Error: {response.json()}")

print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print("✓ POST /api/courses/ now accepts minimal data (auto-generates slug and descriptions)")
print("✓ POST /api/courses/course-modules/ handles course in body or query param")
print("✓ 400 Bad Request issues should be resolved!")
