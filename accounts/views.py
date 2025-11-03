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
from django.views.decorators.csrf import csrf_exempt


from .serializers import (
    SignupSerializer,
    SignInSerializer,
    UserSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .models import UserToken
from .models import UserProfile
import json
import re


@api_view(["GET"])
@authentication_classes([DatabaseTokenAuthentication])
@permission_classes([AllowAny])
def user_detail_view(request, pk):
    """Return public user data for a given user id.

    Frontend expects GET /api/accounts/users/<id>/ to return the user object.
    """
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(status=404)

    data = UserSerializer(user, context={"request": request}).data

    # Attach follower/following counts and whether the requesting user follows this user
    try:
        from .models import Follow
        followers_count = Follow.objects.filter(followed=user).count()
        following_count = Follow.objects.filter(follower=user).count()
    except Exception as e:
        # If Follow table missing or error occurs, default to 0 and log for debugging
        try:
            print(f"[debug] Could not compute follow counts for user {user.pk}: {e}")
        except Exception:
            pass
        followers_count = 0
        following_count = 0

    is_following = False
    try:
        if request.user and request.user.is_authenticated and request.user.pk != user.pk:
            from .models import Follow
            is_following = Follow.objects.filter(follower=request.user, followed=user).exists()
    except Exception:
        is_following = False

    # merge into response
    data['followers_count'] = followers_count
    data['following_count'] = following_count
    data['is_following'] = is_following

    return Response(data)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([DatabaseTokenAuthentication])
@permission_classes([IsAuthenticated])
def toggle_follow_view(request, pk):
    """Toggle follow/unfollow for user with id=pk. Returns updated follow state and counts."""
    if request.user.pk == int(pk):
        return Response({'detail': "Cannot follow yourself"}, status=400)
    try:
        target = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'detail': 'User not found'}, status=404)

    from .models import Follow
    try:
        existing = Follow.objects.filter(follower=request.user, followed=target).first()
        if existing:
            existing.delete()
            is_following = False
        else:
            Follow.objects.create(follower=request.user, followed=target)
            is_following = True
    except Exception as e:
        return Response({'detail': 'Failed to toggle follow', 'error': str(e)}, status=500)

    followers_count = Follow.objects.filter(followed=target).count()
    return Response({'is_following': is_following, 'followers_count': followers_count}, status=200)

User = get_user_model()
TOKEN_LIFETIME = timedelta(days=7)

# ----------------------------- SIGN UP
@csrf_exempt
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

    user_data = UserSerializer(user, context={'request': request}).data
    redirect_url = f"/dashboard/{user.role}" if user.role else "/dashboard"

    return Response({
        "success": True,
        "message": "User registered successfully",
        "user": user_data,
        "token": str(token.token),
        "redirect_url": redirect_url,
    })


@csrf_exempt
@api_view(["POST", "OPTIONS"])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    if request.method == "OPTIONS":
        response = Response()
        response["Access-Control-Allow-Origin"] = request.headers.get('Origin', '*')
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Auth-Token"
        response["Access-Control-Allow-Credentials"] = "true"
        return response

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

    user_data = UserSerializer(user, context={'request': request}).data
    redirect_map = {
        "individual": "/dashboard/individual",
        "facilitator": "/dashboard/facilitator",
        "corporate": "/dashboard/corporate",
    }

    response = Response({
        "success": True,
        "user": user_data,
        "token": str(token.token),
        "redirect_url": redirect_map.get(user.role, "/dashboard"),
    })
    
    # Explicitly set CORS headers for the response
    response["Access-Control-Allow-Origin"] = request.headers.get('Origin', '*')
    response["Access-Control-Allow-Credentials"] = "true"
    
    return response


# ----------------------------- LOGOUT
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Token "):
        token_value = auth_header.split(" ")[1]
        UserToken.objects.filter(token=token_value).delete()
    return Response({"success": True, "message": "Logged out successfully"})



@api_view(["GET", "PATCH"]) 
@authentication_classes([DatabaseTokenAuthentication])  # ✅ Use custom auth
@permission_classes([IsAuthenticated])
def me_view(request):
    # GET: return current user
    if request.method == 'GET':
        user_data = UserSerializer(request.user, context={'request': request}).data
        return Response({"user": user_data})

    # PATCH: allow updating profile fields, including avatar upload
    # Accept both JSON body with profile.avatar_url and multipart/form-data with 'avatar' file
    raw_profile = request.data.get('profile') if 'profile' in request.data else {}
    # When sent as multipart/form-data the 'profile' field may be a JSON string
    if isinstance(raw_profile, str):
        try:
            profile_data = json.loads(raw_profile)
        except Exception:
            profile_data = {}
    elif isinstance(raw_profile, dict):
        profile_data = raw_profile
    else:
        profile_data = {}
    user = request.user

    # Update simple profile fields
    profile = getattr(user, 'profile', None)
    if not profile:
        profile = UserProfile.objects.create(user=user)

    # If a file was uploaded under 'avatar', save it to the ImageField
    avatar_file = request.FILES.get('avatar')
    if avatar_file:
        profile.avatar.save(avatar_file.name, avatar_file, save=True)

    # External avatar URL
    avatar_url = profile_data.get('avatar_url')
    if avatar_url is not None:
        # Basic safety: reject values that clearly contain binary markers or NUL bytes
        if isinstance(avatar_url, str):
            if '\x00' in avatar_url or 'JFIF' in avatar_url.upper() or 'ICC_PROFILE' in avatar_url.upper():
                # don't save corrupted avatar values; log to server logs
                try:
                    print(f"[safety] Rejected binary-like avatar_url for user {user.pk}")
                except Exception:
                    pass
            else:
                # optionally validate URL shape: allow http(s) or path-like values
                if re.match(r'^(https?:)?//', avatar_url) or avatar_url.startswith('/') or avatar_url.startswith('data:image/'):
                    profile.avatar_url = avatar_url
                else:
                    # if it's an odd value (very long or contains binary-looking chars), ignore
                    if len(avatar_url) < 500:
                        profile.avatar_url = avatar_url
        else:
            # non-string avatar_url; ignore
            pass

    # Allow updating full_name etc if provided
    for fld in ['full_name', 'phone', 'country', 'bio', 'company_name', 'industry']:
        if fld in profile_data:
            setattr(profile, fld, profile_data.get(fld))

    profile.save()

    user_data = UserSerializer(user, context={'request': request}).data
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
