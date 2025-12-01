#!/usr/bin/env python
"""Test the fixed endpoint"""
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
print("TEST: Using hyphen format (get-questions) with fixed URL path")
print("=" * 60)

response = client.post(
    f'/api/courses/lessons/{lesson_id}/get-questions/',
    content_type='application/json',
    HTTP_AUTHORIZATION=f'Bearer {token_str}',
    HTTP_ACCEPT='application/json',
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    try:
        data = json.loads(response.content)
        print(f"[OK] SUCCESS!")
        print(f"  Response keys: {list(data.keys())}")
        if 'questions' in data:
            print(f"  Questions count: {len(data['questions'])}")
    except:
        print(f"[ERROR] Response is not JSON")
        print(f"  First 200 chars: {response.content[:200]}")
else:
    print(f"[ERROR] Status {response.status_code}")
    if response.status_code == 302:
        print(f"  Redirect to: {response.get('Location')}")
    print(f"  Content: {response.content[:200]}")
