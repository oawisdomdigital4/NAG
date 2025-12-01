#!/usr/bin/env python
"""Test using Django's test client"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client
import json

client = Client()

token_str = 'ce4cf451-5149-420c-9eaa-141fec24dbd3'
lesson_id = 20

print("=" * 60)
print("Testing with Django test client")
print("=" * 60)

response = client.post(
    f'/api/courses/lessons/{lesson_id}/get-questions/',
    content_type='application/json',
    HTTP_AUTHORIZATION=f'Bearer {token_str}',
    HTTP_ACCEPT='application/json',
)

print(f"Status: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")

if response.status_code == 200:
    try:
        data = json.loads(response.content)
        print(f"✅ Got JSON response!")
        print(f"   Keys: {list(data.keys())}")
        if 'questions' in data:
            print(f"   Questions: {len(data['questions'])}")
    except:
        print(f"❌ Response is not JSON")
        print(f"   First 200 chars: {response.content[:200]}")
else:
    print(f"❌ Status {response.status_code}")
    print(f"   Content: {response.content[:200]}")
