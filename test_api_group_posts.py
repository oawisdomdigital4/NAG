#!/usr/bin/env python
"""
Test script to verify group posts API works correctly via DRF viewset.
This simulates the actual frontend API calls.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model
from community.models import Group, GroupMembership, Post
from community.views import PostViewSet
from rest_framework.request import Request as DRFRequest
from rest_framework.test import APIRequestFactory

User = get_user_model()

def test_api_group_post_flow():
    """Test the complete API flow: create post in group, fetch posts from group."""
    
    print("\n" + "="*70)
    print("TEST: Complete API Group Post Flow")
    print("="*70)
    
    # Setup
    factory = APIRequestFactory()
    
    # 1. Create test users
    print("\n1. Creating test users...")
    user1, _ = User.objects.get_or_create(
        username='apitest1',
        defaults={'email': 'apitest1@test.com', 'is_active': True}
    )
    print(f"   User1: {user1.username} (ID={user1.id})")
    
    # 2. Create test group
    print("\n2. Creating test group...")
    group, _ = Group.objects.get_or_create(
        name='API Test Group',
        defaults={'description': 'Test group for API', 'category': 'test'}
    )
    print(f"   Group: {group.name} (ID={group.id})")
    
    # 3. Simulate POST to create post in group
    print("\n3. Simulating POST /api/community/posts/ with group_id...")
    post_data = {
        'content': 'Test post from API',
        'group': group.id,
        'feed_visibility': 'group_only'
    }
    
    # Create DRF request
    post_request = factory.post('/api/community/posts/', post_data, format='json')
    drf_post_request = DRFRequest(post_request)
    drf_post_request.user = user1
    
    # Call viewset create method
    viewset = PostViewSet()
    viewset.request = drf_post_request
    viewset.format_kwarg = None
    
    response = viewset.create(drf_post_request)
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 201:
        post_id = response.data.get('id')
        print(f"   ✓ Post created successfully (ID={post_id})")
        print(f"      - Group: {response.data.get('group')}")
        print(f"      - Visibility: {response.data.get('feed_visibility')}")
        print(f"      - Author: {response.data.get('author')}")
    else:
        print(f"   ✗ Post creation failed!")
        print(f"      Response: {response.data}")
        return False
    
    # 4. Check if user was auto-added to group
    print("\n4. Checking group membership after POST...")
    user1_in_group = GroupMembership.objects.filter(user=user1, group=group).exists()
    print(f"   User1 in group: {user1_in_group}")
    if user1_in_group:
        print("   ✓ User auto-added to group!")
    else:
        print("   ℹ User NOT auto-added (but may not be needed)")
    
    # 5. Simulate GET to fetch posts from group
    print("\n5. Simulating GET /api/community/posts/?group_id={group_id}...")
    get_request = factory.get(f'/api/community/posts/?group_id={group.id}')
    drf_get_request = DRFRequest(get_request)
    drf_get_request.user = user1
    
    # Call viewset list method
    viewset = PostViewSet()
    viewset.request = drf_get_request
    viewset.format_kwarg = None
    viewset.action = 'list'
    
    response = viewset.list(drf_get_request)
    print(f"   Response status: {response.status_code}")
    print(f"   Posts returned: {len(response.data.get('results', response.data if isinstance(response.data, list) else []))} posts")
    
    # Parse response
    posts = response.data.get('results', response.data if isinstance(response.data, list) else [])
    print(f"\n   Posts in group {group.id}:")
    for p in posts:
        print(f"      - Post {p.get('id')}: {p.get('content', '')[:50]}... (by {p.get('author')})")
    
    # 6. Verify our post is in the results
    print("\n6. Verifying our post is in the response...")
    post_found = any(p.get('id') == post_id for p in posts)
    
    if post_found:
        print(f"   ✓ POST FOUND! Post {post_id} is visible in group feed!")
    else:
        print(f"   ✗ POST NOT FOUND! Post {post_id} is NOT visible in group feed!")
        print(f"      Expected to see post {post_id} but got {len(posts)} posts")
    
    # 7. Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if post_found:
        print("✓ COMPLETE API FLOW WORKS! Posts created in groups are visible!")
    else:
        print("✗ API FLOW BROKEN! Posts not appearing in group feed!")
    
    print("="*70 + "\n")
    
    return post_found

if __name__ == '__main__':
    success = test_api_group_post_flow()
    sys.exit(0 if success else 1)
