from django.contrib import admin
from .models import Plan, Subscription, Payment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
	list_display = ("name", "price", "interval")
	search_fields = ("name",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
	list_display = ("user", "plan", "status", "start_date", "end_date")
	search_fields = ("user__email", "plan__name")
	list_filter = ("status",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ("user", "amount", "provider", "status", "created_at")
	search_fields = ("user__email", "provider", "transaction_id")
	list_filter = ("status", "provider")
