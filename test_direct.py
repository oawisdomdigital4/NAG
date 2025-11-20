#!/usr/bin/env python
"""Direct test of admin dashboard with authenticated user"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from accounts.models import User
from myproject.admin import EnhancedAdminSite
from django.contrib import admin as django_admin

print("=" * 80)
print("DIRECT ADMIN DASHBOARD TEST WITH FIXED ADMIN SITE")
print("=" * 80)

# Check which class admin.site is using
print(f"\n1. Admin site class: {django_admin.site.__class__.__name__}")

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

# Test the admin site index
print(f"\n2. Calling admin.site.index()...")
try:
    response = django_admin.site.index(request)
    print(f"   Status: {response.status_code}")
    
    # Render and check content
    rendered = response.render()
    content = rendered.content.decode('utf-8')
    
    import re
    
    print(f"\n3. Checking rendered content...")
    print(f"   Content length: {len(content)} bytes")
    
    # Check for live stats
    stat_pattern = r'<div class="value">(\d+)</div>'
    stats = re.findall(stat_pattern, content)
    
    if stats:
        print(f"   Found {len(stats)} stat values:")
        for i, val in enumerate(stats[:8], 1):
            print(f"     {i}. {val}")
        print("\n   ✅ LIVE DATA IS DISPLAYING!")
    else:
        print("   ❌ No stat values found")
        
        # Check for unrendered template vars (bad sign)
        template_vars = re.findall(r'\{\{(\w+)\}\}', content)
        if template_vars:
            print(f"\n   Found {len(set(template_vars))} unrendered template variables:")
            for var in set(template_vars)[:5]:
                print(f"     - {var}")
    
    # Check chart data
    chart_js = 'var userGrowthData' in content
    print(f"\n4. Chart data present: {'✅ YES' if chart_js else '❌ NO'}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
