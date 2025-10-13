from django.db import models
from accounts.models import User

class Plan(models.Model):
	name = models.CharField(max_length=100)
	price = models.DecimalField(max_digits=8, decimal_places=2)
	interval = models.CharField(max_length=10)  # 'month', 'year'
	features = models.JSONField(default=list, blank=True)

class Subscription(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_subscriptions')
	plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='payments_plan_subscriptions')
	status = models.CharField(max_length=20)
	start_date = models.DateField()
	end_date = models.DateField()

class Payment(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_payments')
	amount = models.DecimalField(max_digits=8, decimal_places=2)
	provider = models.CharField(max_length=50)
	status = models.CharField(max_length=20)
	transaction_type = models.CharField(max_length=50, blank=True)
	currency = models.CharField(max_length=10, default='USD')
	gateway_reference = models.CharField(max_length=100, blank=True, null=True)
	transaction_id = models.CharField(max_length=100, blank=True, null=True)
	metadata = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
