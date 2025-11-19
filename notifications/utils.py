from .models import Notification, NotificationPreference
from django.db import transaction
from django.conf import settings
from urllib.parse import urljoin


def _normalize_action_url(action_url: str) -> str:
    """Return an absolute URL for action_url. If a relative path is provided (starts with '/'),
    prefix it with `settings.FRONTEND_URL` if available. Otherwise return as-is.
    """
    if not action_url:
        return ''
    try:
        # If it looks like an absolute URL, return as-is
        if action_url.startswith('http://') or action_url.startswith('https://'):
            return action_url
        # If it's a root-relative path, join with FRONTEND_URL when available
        if action_url.startswith('/'):
            base = getattr(settings, 'FRONTEND_URL', '') or ''
            if base:
                return urljoin(base.rstrip('/') + '/', action_url.lstrip('/'))
            # No FRONTEND_URL configured; return the relative path as-is
            return action_url
        return action_url
    except Exception:
        return action_url


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

    # Normalize action_url so URLField validation doesn't reject root-relative paths
    normalized_action = _normalize_action_url(action_url or '')

    with transaction.atomic():
        notif = Notification(
            user=user,
            category=category,
            title=title,
            message=message,
            action_url=normalized_action or '',
            metadata=metadata or {},
        )
        notif.save()

    # Optionally handle email sending logic elsewhere if pref and pref.email_enabled
    return notif
