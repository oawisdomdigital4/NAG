#!/usr/bin/env python
"""Debugging URL routing - detailed"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.urls import resolve

# Check what URL pattern matches our endpoint
path = '/api/courses/lessons/20/get-questions/'
print("=" * 60)
print(f"Resolving: {path}")
print("=" * 60)

try:
    match = resolve(path)
    print(f"✓ Matched!")
    print(f"  View function: {match.func}")
    print(f"  View name: {match.view_name}")
    print(f"  Namespace: {match.namespace}")
    print(f"  Kwargs: {match.kwargs}")
    print(f"  Args: {match.args}")
except Exception as e:
    print(f"✗ ERROR resolving URL: {e}")
    import traceback
    traceback.print_exc()
