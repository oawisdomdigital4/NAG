#!/usr/bin/env python
"""
Test script to verify what happens when POSTing to /community/group/ (wrong endpoint)
vs the correct /api/community/groups/
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from accounts.models import UserToken
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# Create test user with valid token (make them superuser to be absolutely sure)
try:
    user = User.objects.get(username='testuser')
    user.is_staff = True
    user.is_superuser = True
    user.save()
except User.DoesNotExist:
    user = User.objects.create_superuser(username='testuser', email='test@example.com', password='testpass123')

# Ensure user has valid token
token, created = UserToken.objects.get_or_create(user=user)
token.expires_at = timezone.now() + timedelta(days=365)
token.save()

client = Client()

group_data = {
    'name': 'Test Group for Wrong Endpoint',
    'description': 'Testing wrong endpoint',
    'category': 'Learning',
    'is_private': False,
}

headers = {
    'HTTP_AUTHORIZATION': f'Token {token.token}',
}

print("=" * 80)
print("TEST 1: POST to CORRECT endpoint /api/community/groups/")
print("=" * 80)

response = client.post('/api/community/groups/', group_data, format='json', **headers)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

print("\n" + "=" * 80)
print("TEST 2: POST to WRONG endpoint /community/group/ (no /api prefix)")
print("=" * 80)

response = client.post('/community/group/', group_data, format='json', **headers)
print(f"Status Code: {response.status_code}")
print(f"Response Content Type: {response.get('Content-Type', 'N/A')}")
try:
    print(f"Response Body: {response.json()}")
except Exception as e:
    print(f"Response Body (raw): {response.content[:500]}")
    print(f"Error parsing JSON: {e}")

print("\n" + "=" * 80)
print("TEST 3: POST to ADMIN endpoint /admin/community/group/ (HTML form submission)")
print("=" * 80)

response = client.post('/admin/community/group/', group_data, **headers)
print(f"Status Code: {response.status_code}")
print(f"Response Content Type: {response.get('Content-Type', 'N/A')}")
print(f"Response preview: {response.content[:200]}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("✓ Test completed. Check if /community/group/ endpoint exists at all.")
print("✓ The error '/community/group/' suggests this is likely a frontend routing issue")
print("✓ or incorrect endpoint being called from the form.")
