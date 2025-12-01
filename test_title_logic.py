import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from community.models import Post
from community.engagement import CommunityEngagementLog
from django.contrib.auth import get_user_model

User = get_user_model()

# Check some recent activities with posts
print("Testing Post Title/Content Logic:\n")
activities = CommunityEngagementLog.objects.select_related('post').filter(post__isnull=False).order_by('-created_at')[:10]
for activity in activities:
    if activity.post:
        # Simulate the new logic
        title_or_content = activity.post.title or activity.post.content[:50] + '...'
        print(f"Activity {activity.id}:")
        print(f"  Post ID: {activity.post.id}")
        print(f"  Original Title: '{activity.post.title}'")
        print(f"  Content: '{activity.post.content[:50]}...'")
        print(f"  Display Value: '{title_or_content}'")
        print()
