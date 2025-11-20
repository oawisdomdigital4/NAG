#!/usr/bin/env python
"""Check if chart data is being passed to template"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import RequestFactory
from accounts.models import User
from django.contrib import admin as django_admin
import re

# Create/get admin user
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

# Create request
factory = RequestFactory()
request = factory.get('/admin/')
request.user = user
request.session = {}

# Get response
response = django_admin.site.index(request)
rendered = response.render()
content = rendered.content.decode('utf-8')

print("=" * 80)
print("CHART DATA INSPECTION")
print("=" * 80)

# Extract chart data declarations
patterns = {
    'userGrowthData': r'const userGrowthData = (\[.*?\]);',
    'revenueTrendData': r'const revenueTrendData = (\[.*?\]);',
    'topCoursesData': r'const topCoursesData = (\[.*?\]);',
}

print("\nChart Data Variables:")
for var_name, pattern in patterns.items():
    match = re.search(pattern, content, re.DOTALL)
    if match:
        data = match.group(1)
        print(f"\n{var_name}:")
        print(f"  Found: YES")
        print(f"  Length: {len(data)} chars")
        print(f"  Sample: {data[:100]}...")
        
        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(data)
            print(f"  Parsed: {type(parsed).__name__} with {len(parsed)} items")
            if parsed:
                print(f"  First item: {parsed[0]}")
        except:
            print(f"  Parsed: ERROR - Not valid JSON")
    else:
        print(f"\n{var_name}:")
        print(f"  Found: NO")

# Check if chart.js is loaded
if 'chart.js' in content.lower():
    print("\n\nChart.js: LOADED")
else:
    print("\n\nChart.js: NOT LOADED")

# Check if canvas elements exist
canvases = re.findall(r'<canvas id="(\w+)"', content)
print(f"\nCanvas elements found: {len(canvases)}")
for canvas in canvases:
    print(f"  - {canvas}")

print("\n" + "=" * 80)
