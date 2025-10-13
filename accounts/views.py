from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from rest_framework.decorators import api_view, authentication_classes
from accounts.authentication import DatabaseTokenAuthentication


from .serializers import (
    SignupSerializer,
    SignInSerializer,
    UserSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .models import UserToken

User = get_user_model()
TOKEN_LIFETIME = timedelta(days=7)

# ----------------------------- SIGN UP
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def signup_view(request):
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    # ✅ Create token
    token = UserToken.objects.create(
        user=user,
        expires_at=timezone.now() + TOKEN_LIFETIME
    )

    user_data = UserSerializer(user).data
    redirect_url = f"/dashboard/{user.role}" if user.role else "/dashboard"

    return Response({
        "success": True,
        "message": "User registered successfully",
        "user": user_data,
        "token": str(token.token),
        "redirect_url": redirect_url,
    })


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    serializer = SignInSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"success": False, "message": "Invalid credentials"}, status=401)

    if not user.check_password(password):
        return Response({"success": False, "message": "Invalid credentials"}, status=401)

    # Create token
    token = UserToken.objects.create(
        user=user,
        expires_at=timezone.now() + TOKEN_LIFETIME
    )

    user_data = UserSerializer(user).data
    redirect_map = {
        "individual": "/dashboard/individual",
        "facilitator": "/dashboard/facilitator",
        "corporate": "/dashboard/corporate",
    }

    return Response({
        "success": True,
        "user": user_data,
        "token": str(token.token),
        "redirect_url": redirect_map.get(user.role, "/dashboard"),
    })


# ----------------------------- LOGOUT
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Token "):
        token_value = auth_header.split(" ")[1]
        UserToken.objects.filter(token=token_value).delete()
    return Response({"success": True, "message": "Logged out successfully"})



@api_view(["GET"])
@authentication_classes([DatabaseTokenAuthentication])  # ✅ Use custom auth
@permission_classes([IsAuthenticated])
def me_view(request):
    user_data = UserSerializer(request.user).data
    return Response({"user": user_data})



# ----------------------------- PASSWORD RESET REQUEST
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"]
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return Response({"success": True, "message": "If that email exists, a reset link has been sent."})

    token = default_token_generator.make_token(user)
    uid = user.pk
    reset_link = f"{settings.FRONTEND_BASE_URL}/reset-password?uid={uid}&token={token}"

    send_mail(
        subject="Reset your password",
        message=f"Click here to reset your password: {reset_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )

    return Response({"success": True, "message": "If that email exists, a reset link has been sent."})


# ----------------------------- PASSWORD RESET CONFIRM
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    uid = serializer.validated_data["uid"]
    token = serializer.validated_data["token"]
    new_password = serializer.validated_data["new_password"]

    user = get_object_or_404(User, pk=uid)

    if not default_token_generator.check_token(user, token):
        return Response({"success": False, "message": "Invalid token"}, status=400)

    user.set_password(new_password)
    user.save()

    return Response({"success": True, "message": "Password reset successful"})


# ----------------------------- UPDATE PASSWORD (LOGGED-IN USER)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_password_view(request):
    user = request.user
    new_password = request.data.get("new_password")

    if not new_password:
        return Response({"success": False, "message": "New password required"}, status=400)

    user.set_password(new_password)
    user.save()

    return Response({"success": True, "message": "Password updated successfully"})
