from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('me/', views.me_view),
    path('password-reset/', views.password_reset_request_view),
    path('password-reset-confirm/', views.password_reset_confirm_view),
    path('password-update/', views.update_password_view),

]