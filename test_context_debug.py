#!/usr/bin/env python
"""Debug what context is being passed"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import RequestFactory
from accounts.models import User
from myproject.admin import admin_site
import json

# Create admin user
try:
    user = User.objects.get(username='testdash')
except:
    user = User.objects.create_superuser(
        username='testdash',
        email='testdash@test.com',
        password='Test123456',
        role='facilitator'
    )
    user.is_staff = True
    user.save()

# Call index with debugging
extra_context = {}
response = admin_site.index(request, extra_context=extra_context)

print("=" * 80)
print("CONTEXT VARIABLES DEBUG")
print("=" * 80)

print(f"\nTotal variables in extra_context: {len(extra_context)}")

# Print all variables
for key, value in extra_context.items():
    if isinstance(value, str) and len(value) > 100:
        print(f"\n{key}:")
        print(f"  Type: {type(value).__name__}")
        print(f"  Length: {len(value)}")
        print(f"  Sample: {value[:80]}...")
        
        # Try to parse as JSON
        if value.startswith('[') or value.startswith('{'):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    print(f"  Parsed: List with {len(parsed)} items")
                    if parsed:
                        print(f"  First item: {parsed[0]}")
            except Exception as e:
                print(f"  Parse error: {e}")
    else:
        print(f"\n{key}: {value}")

print("\n" + "=" * 80)
print("KEY CHECKS:")
print(f"  user_growth_data present: {'user_growth_data' in extra_context}")
print(f"  revenue_trend_data present: {'revenue_trend_data' in extra_context}")
print(f"  top_courses_data present: {'top_courses_data' in extra_context}")
print("=" * 80)
