
from rest_framework import viewsets, permissions
from .models import Plan, Subscription, Payment
from .serializers import PlanSerializer, SubscriptionSerializer, PaymentSerializer

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Plan.objects.all()
	serializer_class = PlanSerializer
	permission_classes = [permissions.AllowAny]

class SubscriptionViewSet(viewsets.ModelViewSet):
	queryset = Subscription.objects.all()
	serializer_class = SubscriptionSerializer
	permission_classes = [permissions.IsAuthenticated]

class PaymentViewSet(viewsets.ModelViewSet):
	queryset = Payment.objects.all()
	serializer_class = PaymentSerializer
	permission_classes = [permissions.IsAuthenticated]
