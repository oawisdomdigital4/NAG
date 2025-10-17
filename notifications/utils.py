from .models import Notification, NotificationPreference
from django.db import transaction

def send_notification(user, category, title, message, action_url=None, metadata=None, send_email=False):
    """
    Helper to create a Notification if the user's preferences allow it.
    Returns the Notification instance if created, or None if suppressed.
    """
    try:
        pref = NotificationPreference.objects.filter(user=user, notification_type=category).first()
    except Exception:
        pref = None

    # If preference exists and in_app is disabled, skip creating the in-app notification
    if pref is not None and not pref.in_app_enabled:
        return None

    with transaction.atomic():
        notif = Notification(
            user=user,
            category=category,
            title=title,
            message=message,
            action_url=action_url or '',
            metadata=metadata or {},
        )
        notif.save()

    # Optionally handle email sending logic elsewhere if pref and pref.email_enabled
    return notif
