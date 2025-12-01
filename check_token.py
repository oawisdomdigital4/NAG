#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from accounts.models import UserToken
from django.utils import timezone

# Check for the specific token from browser logs
token_str = 'ce4cf451-5149-420c-9eaa-141fec24dbd3'
try:
    user_token = UserToken.objects.get(token=token_str)
    print(f"✅ Token FOUND!")
    print(f"   User: {user_token.user}")
    print(f"   User ID: {user_token.user.id}")
    print(f"   Expires At: {user_token.expires_at}")
    print(f"   Is Expired: {user_token.is_expired()}")
    print(f"   Current Time: {timezone.now()}")
except UserToken.DoesNotExist:
    print(f"❌ Token NOT FOUND in database")
    print(f"\nAll tokens in database:")
    for token in UserToken.objects.all().order_by('-created_at')[:10]:
        print(f"   - {token.token} (User: {token.user}, Expires: {token.expires_at})")

print("\n" + "="*60)
print("Total tokens in database:", UserToken.objects.count())
