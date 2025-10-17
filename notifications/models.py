from django.db import models
from accounts.models import User

class Notification(models.Model):
	CATEGORY_CHOICES = (
		('course', 'Course'),
		('community', 'Community'),
		('billing', 'Billing'),
		('facilitator', 'Facilitator'),
		('corporate', 'Corporate'),
		('system', 'System'),
	)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_notifications')
	type = models.CharField(max_length=50, blank=True)
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
	title = models.CharField(max_length=255)
	message = models.TextField()
	action_url = models.URLField(blank=True, null=True)
	metadata = models.JSONField(default=dict, blank=True)
	read = models.BooleanField(default=False)
	read_at = models.DateTimeField(null=True, blank=True)
	email_sent = models.BooleanField(default=False)
	email_sent_at = models.DateTimeField(null=True, blank=True)
	archived = models.BooleanField(default=False)
	archived_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def save(self, *args, **kwargs):
		# When creating a new notification, respect the user's NotificationPreference for this category.
		# If the user has explicitly disabled in-app notifications for this category, skip saving.
		if getattr(self, '_state', None) and getattr(self._state, 'adding', False):
			try:
				pref = NotificationPreference.objects.filter(user=self.user, notification_type=self.category).first()
				if pref is not None and not pref.in_app_enabled:
					# Do not create an in-app notification when user opted out
					return
			except Exception:
				# On any error (DB uninitialized, migrations not run), fall back to creating the notification
				pass
		super().save(*args, **kwargs)

class NotificationPreference(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
	notification_type = models.CharField(max_length=50)
	in_app_enabled = models.BooleanField(default=True)
	email_enabled = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
