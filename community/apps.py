from django.apps import AppConfig


class CommunityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'community'
    def ready(self):
        # Import signal handlers to ensure they're connected
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
