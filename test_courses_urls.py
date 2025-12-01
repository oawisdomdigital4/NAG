#!/usr/bin/env python
"""Test if courses URLs work correctly"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.urls import resolve
from courses.urls import urlpatterns as courses_patterns

print("=" * 60)
print("Courses URL patterns:")
print("=" * 60)

for pattern in courses_patterns:
    print(f"  {pattern.pattern} -> {pattern.callback if hasattr(pattern, 'callback') else 'nested'}")

# Now test if the courses endpoints resolve correctly
from django.test import Client

client = Client()

# Test a simple GET to see if it works
print("\n" + "=" * 60)
print("Testing GET /api/courses/lessons/")
print("=" * 60)

response = client.get('/api/courses/lessons/')
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")

if response.status_code == 200:
    print("✓ List endpoint works!")
else:
    print(f"✗ Status {response.status_code}")
    print(f"Content: {response.content[:200]}")
