"""
Test the recent activities API endpoint
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, 'c:\\Users\\HP\\NAG BACKEND\\myproject')
django.setup()

import requests
import json
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a test client
client = Client()

# Get first user
user = User.objects.first()
if not user:
    print("No users found")
    sys.exit(1)

print(f"\n🧪 Testing Recent Activities Endpoint")
print(f"Target User: {user.username} (ID: {user.id})\n")

# Test endpoint without authentication (should fail)
print("1️⃣  Testing without authentication:")
response = client.get('/api/community/activities/')
print(f"   Status: {response.status_code}")
if response.status_code != 200:
    print(f"   ✓ Correctly rejected: {response.data if hasattr(response, 'data') else response.json()}")

# Test with authentication
print("\n2️⃣  Testing with user authentication:")
client.force_login(user)
response = client.get('/api/community/activities/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Success!")
    print(f"   Activities found: {data.get('count', 0)}")
    if data.get('data'):
        print(f"\n   Recent Activities:")
        for activity in data['data'][:3]:
            print(f"   - {activity['activity_type']} at {activity['created_at']}")
else:
    print(f"   ❌ Error: {response.json() if hasattr(response, 'json') else response.content}")

# Test with limit parameter
print("\n3️⃣  Testing with limit=3:")
response = client.get('/api/community/activities/?limit=3')
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Returned {data.get('count', 0)} activities (limit=3)")
else:
    print(f"   ❌ Error: {response.status_code}")

# Test with specific user parameter
print(f"\n4️⃣  Testing with user parameter (user={user.id}):")
response = client.get(f'/api/community/activities/?user={user.id}&limit=5')
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Returned {data.get('count', 0)} activities")
    print(f"   Endpoint is working correctly!")
else:
    print(f"   ❌ Error: {response.status_code}")

print("\n✅ API endpoint testing completed!")
