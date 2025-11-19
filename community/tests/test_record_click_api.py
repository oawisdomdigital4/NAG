from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from community.models import Post
from community.engagement import CommunityEngagementLog


class RecordClickAPITest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', password='pass')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.post = Post.objects.create(author=self.user, title='Hello', content='World')

    def test_record_click_and_aggregated_into_post_metrics(self):
        # record a click action via the API
        resp = self.client.post('/api/community/engagement/analytics/record_click/', {'post_id': self.post.id, 'action': 'bookmark'}, format='json')
        self.assertIn(resp.status_code, (200, 201))

        # ensure the engagement log entry exists
        logs = CommunityEngagementLog.objects.filter(post_id=self.post.id, action_type='click_action')
        self.assertTrue(logs.exists())

        # fetch post metrics via the analytics endpoint
        resp2 = self.client.get('/api/community/engagement/analytics/post_metrics/', {'post_id': self.post.id})
        self.assertEqual(resp2.status_code, 200)
        data = resp2.json()
        # metrics should include clicks (>=1)
        metrics = data.get('metrics') or {}
        clicks = metrics.get('clicks') or 0
        self.assertGreaterEqual(clicks, 1)
