#!/usr/bin/env python
"""
Test group creation API to diagnose the foreign key constraint error.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
import json

User = get_user_model()

print("\n" + "="*80)
print("GROUP CREATION API TEST")
print("="*80 + "\n")

try:
    # Get or create a test user
    user = User.objects.first()
    if not user:
        print("✗ No users found in database")
        sys.exit(1)
    
    print(f"Using test user: {user.username} (ID: {user.id})")
    
    # Create API client
    client = APIClient()
    
    # Authenticate with the user
    from accounts.models import UserToken
    from datetime import timedelta
    from django.utils import timezone
    
    # Delete old expired tokens
    UserToken.objects.filter(user=user, expires_at__lt=timezone.now()).delete()
    
    # Create a fresh non-expired token
    token = UserToken.objects.create(
        user=user, 
        expires_at=timezone.now() + timedelta(days=365)  # 1 year validity
    )
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.token}')
    print(f"✓ Authenticated with fresh token: {str(token.token)[:20]}... (expires: {token.expires_at})")
    
    # Prepare group data
    group_data = {
        'name': 'Test API Group',
        'description': 'Testing group creation via API',
        'category': 'general',
        'is_private': False,
        'is_corporate_group': False,
    }
    
    print(f"\nAttempting to create group with data:")
    print(json.dumps(group_data, indent=2))
    
    # Attempt to create group
    response = client.post('/api/community/groups/', group_data, format='json')
    
    print(f"\nResponse Status: {response.status_code}")
    if response.status_code == 302:
        print(f"Redirect location: {response.get('Location')}")
        print(f"Response Content: {response.content[:500]}")
    else:
        try:
            print(f"Response Content:\n{json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response Content: {response.content[:500]}")
    
    if response.status_code in [201, 200]:
        print("\n✓ Group created successfully!")
        group_id = response.json().get('id')
        print(f"Group ID: {group_id}")
    else:
        print(f"\n✗ Group creation failed with status {response.status_code}")
        
except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80 + "\n")
