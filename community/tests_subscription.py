from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta

from accounts.models import User, UserToken

class SubscriptionFallbackTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='subuser@example.com', password='pass1234', role='corporate')
        token = UserToken.objects.create(user=self.user, expires_at=timezone.now()+timedelta(days=1))
        self.token_value = str(token.token)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_value}')

    def test_create_comment_with_payments_subscription_fallback(self):
        # Use the payments app Subscription model as a fallback
        try:
            from payments.models import Subscription as PaymentsSubscription
            from payments.models import Plan as PaymentsPlan
        except Exception:
            self.skipTest('payments app not installed')

        # create a plan and payment subscription
        plan = PaymentsPlan.objects.create(name='Corporate Annual', price=500, interval='year')
        end_date = timezone.now() + timedelta(days=365)
        sub = PaymentsSubscription.objects.create(user=self.user, plan=plan, status='active', start_date=timezone.now().date(), end_date=end_date.date())

        # Create a post and try to post a comment; should succeed
        from community.models import Post, Group
        group = Group.objects.create(name='testgroup', description='g', category='Test', is_corporate_group=False, created_by=self.user)
        post = Post.objects.create(author=self.user, content='p', group=group)

        url = '/api/community/comments/'
        resp = self.client.post(url, {'post_id': post.id, 'content': 'c1'}, format='json')
        self.assertEqual(resp.status_code, 201)