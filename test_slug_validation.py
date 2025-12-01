#!/usr/bin/env python
"""Test that slug uniqueness validation still works"""
import os
import sys
import django

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
print("TEST 1: SLUG UNIQUENESS VALIDATION (should reject duplicate)")
print("=" * 80)

# Create two test users
User = get_user_model()
user1 = User.objects.filter(username='testuser1').first() or User.objects.create_user(
    username='testuser1', email='user1@test.com', password='pass123', role='facilitator')
user2 = User.objects.filter(username='testuser2').first() or User.objects.create_user(
    username='testuser2', email='user2@test.com', password='pass123', role='facilitator')

# Get tokens
import uuid
token1 = UserToken.objects.filter(user=user1).first() or UserToken.objects.create(
    user=user1, token=str(uuid.uuid4()), expires_at=datetime.now() + timedelta(days=30))
token2 = UserToken.objects.filter(user=user2).first() or UserToken.objects.create(
    user=user2, token=str(uuid.uuid4()), expires_at=datetime.now() + timedelta(days=30))

# Create first course
print("\n[*] Creating first course with slug 'unique-slug-test'...")
data1 = {
    'title': 'Test Course 1',
    'slug': 'unique-slug-test',
    'category': 'Technology',
    'level': 'Beginner',
    'format': 'Online',
    'short_description': 'First course',
    'full_description': 'First test course',
    'price': '49.99',
}
response1 = requests.post(
    'http://127.0.0.1:8000/api/courses/',
    data=data1,
    headers={'Authorization': f'Bearer {token1.token}'}
)
print(f"Response: {response1.status_code}")
if response1.status_code == 201:
    print("[+] First course created successfully")
else:
    print(f"[-] Failed: {response1.text}")

# Try to create second course with same slug (should fail)
print("\n[*] Creating second course with SAME slug (should fail with 400)...")
data2 = {
    'title': 'Test Course 2',
    'slug': 'unique-slug-test',
    'category': 'Technology',
    'level': 'Beginner',
    'format': 'Online',
    'short_description': 'Second course',
    'full_description': 'Second test course',
    'price': '99.99',
}
response2 = requests.post(
    'http://127.0.0.1:8000/api/courses/',
    data=data2,
    headers={'Authorization': f'Bearer {token2.token}'}
)
print(f"Response: {response2.status_code}")
if response2.status_code == 400:
    print("[+] Correctly rejected duplicate slug with 400 error")
    print(f"    Error: {response2.json().get('slug', response2.json())}")
else:
    print(f"[-] Should have been 400, got {response2.status_code}: {response2.text}")

print("\n" + "=" * 80)
print("TEST 2: SLUG UPDATE SHOULD NOT FAIL (same slug update)")
print("=" * 80)

# Get existing course
course = Course.objects.filter(slug='unique-slug-test').first()
if course:
    print(f"\n[*] Updating course '{course.slug}' with same slug...")
    update_data = {
        'title': 'Test Course 1 - Updated',
        'slug': 'unique-slug-test',
        'category': 'Technology',
        'level': 'Intermediate',
        'format': 'Online',
        'short_description': 'Updated first course',
        'full_description': 'Updated first test course',
        'price': '59.99',
    }
    response3 = requests.put(
        f'http://127.0.0.1:8000/api/courses/{course.slug}/',
        data=update_data,
        headers={'Authorization': f'Bearer {token1.token}'}
    )
    print(f"Response: {response3.status_code}")
    if response3.status_code == 200:
        print("[+] Update succeeded - slug validation working correctly")
    else:
        print(f"[-] Failed with {response3.status_code}: {response3.text}")
else:
    print("[-] Course not found")

print("\n" + "=" * 80)
