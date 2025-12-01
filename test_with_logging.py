#!/usr/bin/env python
"""Test to trace where the 302 redirect comes from"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client
from django.test.utils import override_settings
import json

# Enable logging to see what's happening
import logging
logging.basicConfig(level=logging.DEBUG)
django_logger = logging.getLogger('django')
django_logger.setLevel(logging.DEBUG)

client = Client()

token_str = 'ce4cf451-5149-420c-9eaa-141fec24dbd3'
lesson_id = 20

print("=" * 60)
print("Testing with Django test client - with logging")
print("=" * 60)

response = client.post(
    f'/api/courses/lessons/{lesson_id}/get-questions/',
    content_type='application/json',
    HTTP_AUTHORIZATION=f'Bearer {token_str}',
    HTTP_ACCEPT='application/json',
)

print(f"\nStatus: {response.status_code}")
print(f"Location header: {response.get('Location')}")
print(f"Content-Type: {response.get('Content-Type')}")

# Check the redirect location
if response.status_code == 302:
    print(f"\n302 Redirect to: {response.get('Location')}")
