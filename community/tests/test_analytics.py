from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from community.models import Post
from datetime import timedelta
from django.utils import timezone


class CommunityAnalyticsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', email='t@e.com', password='pass')
        self.client.force_authenticate(self.user)

    def test_community_analytics_endpoint(self):
        url = reverse('community-analytics')
        resp = self.client.get(url + '?days=7')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('trending_topics', resp.data)

    def test_user_analytics_self(self):
        # Create a post to have something to measure
        Post.objects.create(author=self.user, content='hello world', feed_visibility='public_global')
        url = reverse('user-analytics')
        resp = self.client.get(url + '?days=7')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('post_count', resp.data)
