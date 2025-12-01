#!/usr/bin/env python
"""Debugging URL routing"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.urls import resolve, get_resolver

# Check what URL pattern matches our endpoint
resolver = get_resolver()

path = '/api/courses/lessons/20/get-questions/'
print("=" * 60)
print(f"Resolving: {path}")
print("=" * 60)

try:
    match = resolver.resolve(path)
    print(f"Matched URL pattern: {match.pattern}")
    print(f"Matched view: {match.func}")
    print(f"View name: {match.view_name}")
except Exception as e:
    print(f"ERROR resolving URL: {e}")

print("\n" + "=" * 60)
print("All URL patterns:")
print("=" * 60)

# Print all URL patterns that might match /api/
for pattern in resolver.url_patterns:
    pattern_str = str(pattern.pattern)
    if 'api' in pattern_str or pattern_str == '':
        print(f"  {pattern_str}")
