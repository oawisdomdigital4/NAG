"""
End-to-end test: User likes a post, then check if it appears in recent activities
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.insert(0, 'c:\\Users\\HP\\NAG BACKEND\\myproject')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from community.models import Post, PostReaction
from community.engagement import CommunityEngagementLog
from django.utils import timezone

User = get_user_model()

# Get users
user = User.objects.filter(username='wisdom').first() or User.objects.first()
post = Post.objects.first()

if not user or not post:
    print("❌ Not enough test data. Need at least one user and one post.")
    sys.exit(1)

print(f"\n🧪 End-to-End Test: Like Post → Recent Activities")
print(f"User: {user.username} (ID: {user.id})")
print(f"Post: {post.title[:50]} (ID: {post.id})\n")

client = Client()
client.force_login(user)

# Step 1: Count activities before liking
print("1️⃣  Checking activities BEFORE liking:")
response = client.get(f'/api/community/activities/?user={user.id}&limit=5')
if response.status_code == 200:
    data = response.json()
    before_activities = data.get('results', [])
    print(f"   ✓ Found {len(before_activities)} activities")
else:
    print(f"   ❌ Failed to fetch activities: {response.status_code}")
    sys.exit(1)

# Step 2: Create a like (simulating the user liking the post)
print("\n2️⃣  Creating a like action:")
try:
    # Remove existing reaction if any
    PostReaction.objects.filter(user=user, post=post, reaction_type='like').delete()
    
    # Create new reaction
    reaction = PostReaction.objects.create(
        user=user,
        post=post,
        reaction_type='like'
    )
    print(f"   ✓ Created PostReaction (ID: {reaction.id})")
    
    # Verify engagement log was created
    logs = CommunityEngagementLog.objects.filter(
        user=user,
        action_type='like_post',
        post=post
    ).order_by('-created_at')
    
    if logs.exists():
        latest_log = logs.first()
        print(f"   ✓ Engagement logged (ID: {latest_log.id}, Time: {latest_log.created_at})")
    else:
        print(f"   ⚠️  No engagement log found yet")
        
except Exception as e:
    print(f"   ❌ Error creating like: {e}")
    sys.exit(1)

# Step 3: Check activities AFTER liking
print("\n3️⃣  Checking activities AFTER liking:")
response = client.get(f'/api/community/activities/?user={user.id}&limit=5')
if response.status_code == 200:
    data = response.json()
    after_activities = data.get('results', [])
    print(f"   ✓ Found {len(after_activities)} activities")
    
    # Check if the new like appears
    like_activity = None
    for activity in after_activities:
        if activity['activity_type'] == 'like_post' and activity.get('post', {}).get('id') == post.id:
            like_activity = activity
            break
    
    if like_activity:
        print(f"\n✅ SUCCESS! Like activity found in recent activities:")
        print(f"   - Activity Type: {like_activity['activity_type']}")
        print(f"   - Post: {like_activity.get('post', {}).get('title', 'N/A')}")
        print(f"   - Time: {like_activity['created_at']}")
        print(f"\n🎉 The 'like' action correctly appears in recent activities!")
    else:
        print(f"\n❌ FAILED! Like activity NOT found in recent activities")
        print(f"   Expected to find a 'like_post' activity for post ID {post.id}")
        print(f"\n   Activities returned:")
        for i, activity in enumerate(after_activities[:3], 1):
            print(f"   {i}. {activity['activity_type']}")
        
else:
    print(f"   ❌ Failed to fetch activities: {response.status_code}")
    sys.exit(1)

# Step 4: Show the complete data structure
print(f"\n4️⃣  Sample activity data structure:")
if after_activities:
    import json
    print(json.dumps(after_activities[0], indent=2, default=str))

print("\n✅ Test completed!")
