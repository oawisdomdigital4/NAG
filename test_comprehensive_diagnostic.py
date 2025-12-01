#!/usr/bin/env python
"""
Comprehensive diagnostic test for group post creation and fetching.
Tests both the backend logic and potential caching issues.
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.cache import cache
from community.models import Group, GroupMembership, Post

User = get_user_model()

def diagnose_group_posts():
    """Comprehensive diagnostic of group post creation and fetching."""
    
    print("\n" + "="*80)
    print("COMPREHENSIVE GROUP POSTS DIAGNOSTIC")
    print("="*80)
    
    # =========================================================================
    # 1. CHECK EXISTING POSTS IN DATABASE
    # =========================================================================
    print("\n1. CHECKING DATABASE STATE")
    print("-" * 80)
    
    total_posts = Post.objects.count()
    posts_with_group = Post.objects.filter(group__isnull=False).count()
    posts_without_group = Post.objects.filter(group__isnull=True).count()
    
    print(f"Total posts in database: {total_posts}")
    print(f"  - Posts WITH group_id: {posts_with_group}")
    print(f"  - Posts WITHOUT group_id: {posts_without_group}")
    
    if posts_with_group > 0:
        print("\n   Sample posts with group_id:")
        for p in Post.objects.filter(group__isnull=False).select_related('author', 'group')[:3]:
            print(f"      Post {p.id}: group={p.group.id} ({p.group.name}), "
                  f"author={p.author.username}, "
                  f"visibility={p.feed_visibility}, "
                  f"approved={p.is_approved}")
    
    # =========================================================================
    # 2. CREATE NEW TEST POST IN GROUP
    # =========================================================================
    print("\n2. CREATING TEST POST IN GROUP")
    print("-" * 80)
    
    # Get or create test user and group
    test_user, user_created = User.objects.get_or_create(
        username='diagnostic_user',
        defaults={'email': 'diagnostic@test.com'}
    )
    print(f"Test user: {test_user.username} (ID={test_user.id}) - {'CREATED' if user_created else 'EXISTS'}")
    
    test_group, group_created = Group.objects.get_or_create(
        name='Diagnostic Test Group',
        defaults={'description': 'For diagnostic testing', 'category': 'test'}
    )
    print(f"Test group: {test_group.name} (ID={test_group.id}) - {'CREATED' if group_created else 'EXISTS'}")
    
    # Create a test post
    test_post = Post.objects.create(
        author=test_user,
        content='DIAGNOSTIC TEST POST - Created at ' + str(datetime.now()),
        group=test_group,
        feed_visibility='group_only',
        is_approved=True
    )
    print(f"Test post CREATED: ID={test_post.id}")
    print(f"  - Author: {test_post.author.username} (ID={test_post.author_id})")
    print(f"  - Group: {test_post.group.name} (ID={test_post.group_id})")
    print(f"  - Visibility: {test_post.feed_visibility}")
    print(f"  - Approved: {test_post.is_approved}")
    
    # Verify it was saved
    test_post.refresh_from_db()
    print(f"\n   After refresh from DB:")
    print(f"   - group_id is set: {test_post.group_id is not None}")
    print(f"   - group_id value: {test_post.group_id}")
    print(f"   - group is set: {test_post.group is not None}")
    print(f"   - group value: {test_post.group}")
    
    # =========================================================================
    # 3. TEST VISIBILITY FILTER
    # =========================================================================
    print("\n3. TESTING VISIBILITY FILTER")
    print("-" * 80)
    
    # Simulate what get_queryset does for the author
    base_q = Q(is_approved=True)
    visibility_q = Q(feed_visibility='public_global')
    visibility_q = (
        visibility_q
        | Q(feed_visibility='group_only', group__memberships__user=test_user)
        | Q(author=test_user)
    )
    
    visible_posts = Post.objects.filter(base_q & visibility_q).filter(group=test_group)
    print(f"Posts visible to author in this group: {visible_posts.count()}")
    
    if visible_posts.filter(id=test_post.id).exists():
        print(f"   [PASS] Test post (ID={test_post.id}) IS VISIBLE to author")
    else:
        print(f"   [FAIL] Test post (ID={test_post.id}) NOT VISIBLE to author")
        print(f"   Visible posts: {list(visible_posts.values_list('id', flat=True))}")
    
    # =========================================================================
    # 4. TEST GROUP FILTER
    # =========================================================================
    print("\n4. TESTING GROUP FILTER")
    print("-" * 80)
    
    # Simulate the full API query with group_id parameter
    all_visible = Post.objects.filter(base_q & visibility_q)
    group_filtered = all_visible.filter(group__id=test_group.id)
    
    print(f"Posts after visibility filter: {all_visible.count()}")
    print(f"Posts after group filter: {group_filtered.count()}")
    
    if group_filtered.filter(id=test_post.id).exists():
        print(f"   [PASS] Test post appears in group feed")
    else:
        print(f"   [FAIL] Test post MISSING from group feed")
        print(f"   Available in group: {list(group_filtered.values_list('id', flat=True))}")
    
    # =========================================================================
    # 5. CHECK CACHING
    # =========================================================================
    print("\n5. CHECKING CACHING STATE")
    print("-" * 80)
    
    # Check if any posts might be cached
    cache_key = f'post_list_user_{test_user.id}_group_{test_group.id}'
    cached_posts = cache.get(cache_key)
    
    if cached_posts:
        print(f"   Cache HIT for {cache_key}")
        print(f"   Cached posts: {len(cached_posts) if isinstance(cached_posts, list) else 'not a list'}")
    else:
        print(f"   Cache MISS for {cache_key}")
    
    # Check general feed cache
    feed_cache_key = f'post_feed_user_{test_user.id}'
    feed_cached = cache.get(feed_cache_key)
    if feed_cached:
        print(f"   Cache HIT for general feed: {feed_cache_key}")
    else:
        print(f"   Cache MISS for general feed: {feed_cache_key}")
    
    # =========================================================================
    # 6. CHECK GROUP MEMBERSHIP
    # =========================================================================
    print("\n6. CHECKING GROUP MEMBERSHIP")
    print("-" * 80)
    
    membership_exists = GroupMembership.objects.filter(user=test_user, group=test_group).exists()
    print(f"Author is group member: {membership_exists}")
    
    if not membership_exists:
        print("   NOTE: Author is not a group member, but can still see own posts via Q(author=user)")
        membership_count = GroupMembership.objects.filter(group=test_group).count()
        print(f"   Total group members: {membership_count}")
    
    # =========================================================================
    # 7. SUMMARY
    # =========================================================================
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)
    
    checks = {
        'Post created in DB': test_post.group_id == test_group.id,
        'Post marked approved': test_post.is_approved,
        'Post visible via visibility filter': visible_posts.filter(id=test_post.id).exists(),
        'Post visible via group filter': group_filtered.filter(id=test_post.id).exists(),
    }
    
    all_pass = all(checks.values())
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {check}")
    
    print("\n" + "="*80)
    if all_pass:
        print("RESULT: Backend is working correctly!")
        print("  Issue is likely in: Frontend state management, caching, or API response handling")
    else:
        print("RESULT: Backend has issues!")
        print("  Check the failed items above")
    print("="*80 + "\n")
    
    return all_pass

if __name__ == '__main__':
    success = diagnose_group_posts()
    sys.exit(0 if success else 1)
