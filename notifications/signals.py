from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification, NotificationPreference


@receiver(post_save, sender=Notification)
def enforce_preferences_on_create(sender, instance, created, **kwargs):
    # If notification was created and user's preference disallows in-app, remove it.
    if not created:
        return
    try:
        pref = NotificationPreference.objects.filter(user=instance.user, notification_type=instance.category).first()
    except Exception:
        pref = None

    if pref is not None and not pref.in_app_enabled:
        # Delete the instance to enforce preference
        try:
            instance.delete()
        except Exception:
            pass
