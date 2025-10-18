from django.contrib import admin
from django.utils.html import format_html

# If you have models in payments.models, register them with an icon column.
# Example placeholder admin for any future Payment model:


# from .models import Payment


class PaymentAdminPlaceholder(admin.ModelAdmin):
	list_display = ("icon",)

	def icon(self, obj):
		return format_html("<i class='fas fa-credit-card' style='font-size:16px;color:#0D1B52;'></i>")
	icon.short_description = ''

# If you add a Payment model later, register it like this:
# admin.site.register(Payment, PaymentAdminPlaceholder)
