from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from community.models import Post


class FeedTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='feeduser', email='f@e.com', password='pass')
        self.client.force_authenticate(self.user)

    def test_feed_list_public(self):
        Post.objects.create(author=self.user, content='public post', feed_visibility='public_global')
        url = reverse('post-list')
        resp = self.client.get(url)
        # Should succeed and return a list (200)
        self.assertIn(resp.status_code, (200, 201))
