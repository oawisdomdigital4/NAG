from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from .otp_views import OTPViewSet

# Create router for OTP viewset
router = DefaultRouter()
router.register(r'otp', OTPViewSet, basename='otp')

urlpatterns = [
    path('signup/', views.signup_view),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('me/', views.me_view),
    path('users/<int:pk>/', views.user_detail_view),
    path('users/<int:pk>/follow/', views.toggle_follow_view),
    path('password-reset/', views.password_reset_request_view),
    path('password-reset-confirm/', views.password_reset_confirm_view),
    path('password-update/', views.update_password_view),
] + router.urls