#!/usr/bin/env python
"""Quick test to see if authentication is working"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import force_authenticate
from accounts.authentication import DatabaseTokenAuthentication
from accounts.models import UserToken, User
from django.http import HttpRequest

# Create a test request with Authorization header
factory = RequestFactory()
request = factory.post('/api/courses/lessons/20/get-questions/')

# Add the Authorization header
token_str = 'ce4cf451-5149-420c-9eaa-141fec24dbd3'
request.META['HTTP_AUTHORIZATION'] = f'Bearer {token_str}'

print("=" * 60)
print("Testing DatabaseTokenAuthentication directly")
print("=" * 60)

auth = DatabaseTokenAuthentication()
try:
    result = auth.authenticate(request)
    if result:
        user, token = result
        print(f"✅ Authentication SUCCESS!")
        print(f"   User: {user}")
        print(f"   User ID: {user.id}")
        print(f"   Token: {token}")
    else:
        print(f"❌ Authentication returned None")
except Exception as e:
    print(f"❌ Authentication raised exception: {e}")

print()
print("=" * 60)
print("Checking token in database")
print("=" * 60)

try:
    user_token = UserToken.objects.get(token=token_str)
    print(f"✅ Token found in database")
    print(f"   Token: {user_token.token}")
    print(f"   User: {user_token.user}")
    print(f"   Expired: {user_token.is_expired()}")
except UserToken.DoesNotExist:
    print(f"❌ Token NOT found in database")
