from django.test import TestCase
from django.contrib.auth import get_user_model

from promotions.analytics_service import AnalyticsService


class AnalyticsClicksTest(TestCase):
	def setUp(self):
		User = get_user_model()
		# author is the owner of posts
		self.author = User.objects.create_user(username='author', email='author@example.com', password='pass')
		# actor is the user who will perform clicks
		self.actor = User.objects.create_user(username='actor', email='actor@example.com', password='pass')

		# Create a simple post authored by author
		from community.models import Post
		self.post = Post.objects.create(author=self.author, title='Test Post', content='Hello world')

	def test_clicks_aggregated_into_post_engagement(self):
		# Log a few click_action events via CommunityEngagementLog
		from community.engagement import CommunityEngagementLog

		# Ensure there are no clicks initially
		engagement_before = AnalyticsService.get_user_post_engagement(self.author, days=7)
		# find matching post entry (may be empty list)
		before_entry = next((p for p in engagement_before if p['post_id'] == self.post.id), None)
		before_clicks = before_entry.get('clicks', 0) if before_entry else 0

		# Create 3 click_action logs
		for _ in range(3):
			CommunityEngagementLog.log_engagement(user=self.actor, action_type='click_action', post=self.post, metadata={'action': 'like'})

		# Fetch engagement after clicks
		engagement_after = AnalyticsService.get_user_post_engagement(self.author, days=7)
		after_entry = next((p for p in engagement_after if p['post_id'] == self.post.id), None)
		self.assertIsNotNone(after_entry, 'Post entry must exist in engagement data')
		# clicks field should reflect the 3 new clicks (or increased by 3)
		self.assertEqual(after_entry.get('clicks', 0), before_clicks + 3)
