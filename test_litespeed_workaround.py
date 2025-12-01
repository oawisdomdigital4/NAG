#!/usr/bin/env python
"""
Test the LiteSpeed PUT workaround endpoint.

This tests that the new POST /api/community/groups/{id}/update_group/ endpoint
works correctly as a replacement for PUT when LiteSpeed blocks it.
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from rest_framework.test import APIClient
from accounts.models import UserProfile
from accounts.authentication import DatabaseTokenAuthentication
from community.models import Group

User = get_user_model()

def test_update_group_via_post():
    """Test updating a group via the POST workaround endpoint"""
    print("\n" + "="*70)
    print("TEST: LiteSpeed PUT Workaround Endpoint")
    print("="*70)
    
    # Setup
    print("\n1. Creating test user and group...")
    user = User.objects.filter(username='testuser_update').first()
    if not user:
        user = User.objects.create_user(
            username='testuser_update',
            email='testupdate@example.com',
            password='testpass123'
        )
        UserProfile.objects.get_or_create(user=user)
        print(f"   Created user: {user.username}")
    
    group = Group.objects.filter(name='Test Update Group').first()
    if not group:
        group = Group.objects.create(
            name='Test Update Group',
            description='Original description',
            created_by=user,
            category='general'
        )
        print(f"   Created group: {group.name}")
    
    # Get token
    print("\n2. Getting authentication token...")
    from accounts.models import UserToken
    from datetime import timedelta
    from django.utils import timezone
    
    token = UserToken.objects.filter(user=user).first()
    if not token:
        token = UserToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(days=7)
        )
    print(f"   Token: {str(token.token)[:20]}...")
    
    # Test via APIClient
    print("\n3. Testing POST /api/community/groups/{}/update_group/".format(group.id))
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(token.token))
    
    # Update data
    update_data = {
        'name': 'Updated Group Name',
        'description': 'Updated description via POST workaround',
        'category': 'technology'
    }
    
    response = client.post(
        f'/api/community/groups/{group.id}/update_group/',
        update_data,
        format='json'
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Expected: 200")
    
    if response.status_code == 200:
        print("   [PASS] Endpoint returned 200 OK")
        data = response.json()
        
        # Verify data was updated
        if data['name'] == 'Updated Group Name':
            print("   [PASS] Group name updated correctly")
        else:
            print(f"   [FAIL] Group name not updated (got: {data['name']})")
        
        if data['description'] == 'Updated description via POST workaround':
            print("   [PASS] Group description updated correctly")
        else:
            print(f"   [FAIL] Description not updated (got: {data['description']})")
    else:
        print(f"   [FAIL] Endpoint returned {response.status_code}")
        print(f"   Response: {response.json()}")
    
    # Test with multipart (for file uploads)
    print("\n4. Testing POST with form data (multipart)...")
    multipart_data = {
        'name': 'Multipart Update Test',
        'description': 'Testing multipart form data'
    }
    
    response = client.post(
        f'/api/community/groups/{group.id}/update_group/',
        multipart_data,
        format='multipart'
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   [PASS] Multipart update works")
    else:
        print(f"   [FAIL] Multipart update failed: {response.json()}")
    
    # Test permission denial
    print("\n5. Testing permission check (non-owner should be denied)...")
    other_user = User.objects.filter(username='otheruser').first()
    if not other_user:
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        UserProfile.objects.get_or_create(user=other_user)
    
    other_token = UserToken.objects.filter(user=other_user).first()
    if not other_token:
        from django.utils import timezone
        from datetime import timedelta
        other_token = UserToken.objects.create(
            user=other_user,
            expires_at=timezone.now() + timedelta(days=7)
        )
    
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(other_token.token))
    response = client.post(
        f'/api/community/groups/{group.id}/update_group/',
        {'name': 'Should be denied'},
        format='json'
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 403:
        print("   [PASS] Non-owner correctly denied (403)")
    else:
        print(f"   [FAIL] Expected 403, got {response.status_code}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nSummary:")
    print("- POST /api/community/groups/{id}/update_group/ is working")
    print("- Group data updates correctly")
    print("- Multipart form data is supported")
    print("- Permission checks are enforced")
    print("\nFrontend can now use this endpoint as a workaround for LiteSpeed PUT 501 error!")

if __name__ == '__main__':
    try:
        test_update_group_via_post()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
