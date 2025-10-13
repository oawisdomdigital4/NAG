from django.dispatch import receiver
from django.db.models.signals import post_save
from accounts.models import UserProfile

from community.models import Subscription

@receiver(post_save, sender=Subscription)
def handle_subscription_change(sender, instance, created, **kwargs):
    """Set community_approved on the user's profile when subscription becomes active.

    This handler marks profile.community_approved = True when Subscription.status == 'active'
    and marks False when subscription is cancelled/expired.
    """
    try:
        profile = UserProfile.objects.get(user=instance.user)
    except UserProfile.DoesNotExist:
        # No profile to update
        return

    if instance.status == 'active':
        profile.community_approved = True
        profile.save()
    else:
        # For other statuses, revoke community access
        profile.community_approved = False
        profile.save()
