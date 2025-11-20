#!/usr/bin/env python
"""Check what the response contains"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import RequestFactory
from accounts.models import User
from myproject.admin import admin_site

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

# Create request
factory = RequestFactory()
request = factory.get('/admin/')
request.user = user
request.session = {}

# Call index
response = admin_site.index(request)

print("=" * 80)
print("RESPONSE ANALYSIS")
print("=" * 80)

print(f"\nResponse type: {type(response)}")
print(f"Response status code: {response.status_code}")
print(f"Has context_data: {hasattr(response, 'context_data')}")

if hasattr(response, 'context_data'):
    context = response.context_data
    print(f"Context keys: {list(context.keys())[:10]}...")
    print(f"Total keys: {len(context.keys())}")
    
    # Look for our data
    our_keys = [k for k in context.keys() if 'user' in k or 'post' in k or 'growth' in k or 'revenue' in k]
    print(f"\nOur custom keys:")
    for k in our_keys:
        print(f"  - {k}: {str(context[k])[:50]}")
        
# Render and check HTML
rendered = response.render()
content = rendered.content.decode('utf-8')

import re
stat_values = re.findall(r'<div class="value">(\d+)', content)
print(f"\nLive stat values in HTML: {stat_values[:5]}")

print("\n" + "=" * 80)
