#!/usr/bin/env python
"""Test which URL format works"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client

client = Client()

token_str = 'ce4cf451-5149-420c-9eaa-141fec24dbd3'
lesson_id = 20

print("=" * 60)
print("TEST 1: Using underscore format (get_questions)")
print("=" * 60)

response = client.post(
    f'/api/courses/lessons/{lesson_id}/get_questions/',
    content_type='application/json',
    HTTP_AUTHORIZATION=f'Bearer {token_str}',
    HTTP_ACCEPT='application/json',
)

print(f"Status: {response.status_code}")
if response.status_code == 302:
    print(f"Redirect to: {response.get('Location')}")
else:
    print(f"Response: {response.content[:100]}")

print("\n" + "=" * 60)
print("TEST 2: Using hyphen format (get-questions)")
print("=" * 60)

response = client.post(
    f'/api/courses/lessons/{lesson_id}/get-questions/',
    content_type='application/json',
    HTTP_AUTHORIZATION=f'Bearer {token_str}',
    HTTP_ACCEPT='application/json',
)

print(f"Status: {response.status_code}")
if response.status_code == 302:
    print(f"Redirect to: {response.get('Location')}")
else:
    print(f"Response: {response.content[:100]}")
