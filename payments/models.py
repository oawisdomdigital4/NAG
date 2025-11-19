from django.db import models
from django.conf import settings


class Plan(models.Model):
	"""Canonical Plan model for the payments app.

	This mirrors the fields created in payments/migrations/0001_initial.py
	so that code and migrations are in sync.
	"""
	name = models.CharField(max_length=100)
	price = models.DecimalField(max_digits=8, decimal_places=2)
	interval = models.CharField(max_length=10)
	features = models.JSONField(default=list, blank=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return f"{self.name} ({self.price} {getattr(self, 'currency', '')})"


class Payment(models.Model):
	amount = models.DecimalField(max_digits=8, decimal_places=2)
	provider = models.CharField(max_length=50)
	status = models.CharField(max_length=20)
	transaction_type = models.CharField(max_length=50, blank=True)
	currency = models.CharField(max_length=10, default='USD')
	gateway_reference = models.CharField(max_length=100, blank=True, null=True)
	transaction_id = models.CharField(max_length=100, blank=True, null=True)
	metadata = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_payments')

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.amount} {self.currency} - {self.status} ({self.provider})"


class Subscription(models.Model):
	status = models.CharField(max_length=20)
	start_date = models.DateField()
	end_date = models.DateField()
	plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='payments_plan_subscriptions')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_subscriptions')

	class Meta:
		ordering = ['-start_date']

	def __str__(self):
		return f"{getattr(self.user, 'email', 'user')} - {self.plan.name}"

