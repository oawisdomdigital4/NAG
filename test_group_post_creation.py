#!/usr/bin/env python
"""
Test script to verify post creation with group_id
"""
import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'
django.setup()

from django.contrib.auth import get_user_model
from community.models import Post, Group, GroupMembership
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()

def test_group_post_creation():
    print("\n" + "="*70)
    print("TEST: CREATE POST WITH GROUP_ID")
    print("="*70)
    
    # Create test user
    user, _ = User.objects.get_or_create(
        username='test_post_creator',
        defaults={'email': 'creator@test.com'}
    )
    user.set_password('testpass123')
    user.save()
    print(f"\n✓ Created test user: {user.username} (id={user.id})")
    
    # Create test group
    group, _ = Group.objects.get_or_create(
        name='Test Post Group',
        defaults={'description': 'Group for testing posts', 'created_by': user}
    )
    print(f"✓ Created test group: {group.name} (id={group.id})")
    
    # Add user to group
    GroupMembership.objects.get_or_create(
        group=group,
        user=user
    )
    print(f"✓ Added user to group")
    
    # Setup API client with authentication
    client = APIClient()
    # Use session-based authentication for tests
    client.force_authenticate(user=user)
    print(f"✓ Authenticated API client")
    
    # Test 1: Create post WITH group_id
    print(f"\n--- Test 1: Create post WITH group_id ---")
    post_data = {
        'content': 'This is a test post in a group',
        'group_id': group.id,
        'feed_visibility': 'group_only',
        'post_category': 'general',
    }
    response = client.post('/api/community/posts/', post_data, format='json')
    print(f"Response status: {response.status_code}")
    if response.status_code == 201:
        post_json = response.json()
        post_id = post_json.get('id')
        group_id = post_json.get('group')
        print(f"✓ Post created: id={post_id}")
        print(f"✓ Post group_id: {group_id} (expected: {group.id})")
        if group_id == group.id:
            print(f"✓✓ GROUP_ID CORRECTLY SET!")
        else:
            print(f"✗✗ GROUP_ID NOT SET CORRECTLY (expected {group.id}, got {group_id})")
    else:
        print(f"✗ Post creation failed: {response.json()}")
    
    # Test 2: Fetch posts for specific group
    print(f"\n--- Test 2: Fetch posts for group ---")
    response = client.get(f'/api/community/posts/?group_id={group.id}')
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        print(f"✓ Fetched {len(results)} posts for group {group.id}")
        for p in results:
            print(f"  - Post {p['id']}: {p.get('content', '')[:50]}")
            if p.get('group') == group.id:
                print(f"    ✓ Correct group assignment")
    else:
        print(f"✗ Failed to fetch posts: {response.json()}")
    
    # Test 3: Verify only group posts are returned (not all posts)
    print(f"\n--- Test 3: Verify group filtering ---")
    total_posts = Post.objects.count()
    group_posts = Post.objects.filter(group__id=group.id)
    print(f"Total posts in DB: {total_posts}")
    print(f"Posts in this group: {group_posts.count()}")
    for p in group_posts:
        print(f"  - Post {p.id}: group_id={p.group_id}, visibility={p.feed_visibility}")
    
    print("\n" + "="*70)
    print("✓ TEST COMPLETE")
    print("="*70 + "\n")

if __name__ == '__main__':
    test_group_post_creation()
