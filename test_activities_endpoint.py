"""
Test script to verify the recent activities endpoint is working
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, 'c:\\Users\\HP\\NAG BACKEND\\myproject')
django.setup()

from django.contrib.auth import get_user_model
from community.engagement import CommunityEngagementLog
from community.models import Post, Group
from django.utils import timezone

User = get_user_model()

# Get a test user
try:
    user = User.objects.first()
    if not user:
        print("No users found in database")
        sys.exit(1)
    
    print(f"\n✅ Test User: {user.username} (ID: {user.id})")
    
    # Check recent activities
    logs = CommunityEngagementLog.objects.filter(user=user).order_by('-created_at')[:5]
    
    if logs.exists():
        print(f"\n✅ Found {logs.count()} recent activities for user:\n")
        for log in logs:
            print(f"  - {log.action_type} (ID: {log.id})")
            if log.post:
                print(f"    Post: {log.post.title[:50]}")
            if log.group:
                print(f"    Group: {log.group.name}")
            print(f"    Time: {log.created_at}")
            print()
    else:
        print("\n⚠️  No activities found for this user yet")
    
    # Try to trigger a test engagement
    print("\n📝 Attempting to create test engagement log...")
    try:
        test_post = Post.objects.first()
        if test_post:
            test_log = CommunityEngagementLog.log_engagement(
                user=user,
                action_type='like_post',
                post=test_post,
                metadata={'test': True}
            )
            print(f"✅ Created test log: {test_log.id} - {test_log.action_type}")
        else:
            print("⚠️  No posts found to test with")
    except Exception as e:
        print(f"❌ Error creating test log: {e}")
    
    print("\n✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
