#!/usr/bin/env python
"""Test the admin page via HTTP request"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import AnonymousUser
from accounts.models import User

client = Client()

print("=" * 80)
print("ADMIN DASHBOARD HTTP REQUEST TEST")
print("=" * 80)

# Step 1: Try accessing admin without login
print("\n1. Accessing /admin/ without authentication...")
response = client.get('/admin/')
print(f"   Status: {response.status_code}")
if response.status_code == 302:
    print(f"   Redirected to: {response.url}")

# Step 2: Check if we can create a user
print("\n2. Checking/creating admin user...")
try:
    admin_user = User.objects.get(username='admin')
    print(f"   Found existing admin user")
except User.DoesNotExist:
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@nag.local',
        password='AdminPass123',
        role='facilitator'
    )
    print(f"   Created new admin user")

# Step 3: Login
print("\n3. Logging in as admin...")
login_ok = client.login(username='admin', password='AdminPass123')
if login_ok:
    print(f"   Login successful!")
else:
    print(f"   Login FAILED!")
    # Try alternative auth method
    print("   Trying alternative approaches...")
    
    # Check if user exists and is staff
    print(f"   User exists: {User.objects.filter(username='admin').exists()}")
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.is_active = True
    admin_user.save()
    print(f"   Ensured user is staff and superuser")
    
    # Try login again
    login_ok = client.login(username='admin', password='AdminPass123')
    print(f"   Second login attempt: {'SUCCESS' if login_ok else 'FAILED'}")

# Step 4: Access admin with authentication
print("\n4. Accessing /admin/ with authentication...")
response = client.get('/admin/')
print(f"   Status: {response.status_code}")

if response.status_code == 200:
    content = response.content.decode('utf-8')
    print(f"   Content length: {len(content)} bytes")
    
    print("\n5. Checking for live data in response...")
    
    import re
    
    # Look for stat values
    stat_values = re.findall(r'<div class="value">([^<]+)</div>', content)
    if stat_values:
        print(f"   Found {len(stat_values)} stat card values:")
        for i, val in enumerate(stat_values[:8], 1):
            print(f"     {i}. {val}")
    else:
        print("   No stat values found!")
    
    # Check for template variables (bad sign if present)
    template_vars = re.findall(r'\{\{(\w+)\}\}', content)
    if template_vars:
        print(f"\n   WARNING: Found {len(template_vars)} unrendered template variables:")
        for var in set(template_vars)[:5]:
            print(f"     - {var}")
    
    # Check for chart data
    if 'userGrowthChart' in content and 'var userGrowthData' in content:
        print("\n   Chart data found in template")
        # Extract sample
        match = re.search(r'var userGrowthData = (\[.*?\]);', content, re.DOTALL)
        if match:
            data = match.group(1)[:100]
            print(f"   Sample: {data}...")
    
    print("\n" + "=" * 80)
    if stat_values and not template_vars:
        print("RESULT: SUCCESS - LIVE DATA IS DISPLAYING!")
    else:
        print("RESULT: ISSUE - Check warnings above")
else:
    print(f"   Failed to access admin dashboard!")
    print(f"   Response: {response.status_code}")
