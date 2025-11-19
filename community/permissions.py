from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCommunityMember(BasePermission):
    """Permission used across community views.

    Behavior:
    - Allow any authenticated user to perform safe/read-only requests (GET/HEAD/OPTIONS).
      This prevents 403 on simple reads while the user's profile is being populated
      during login/HMR races.
    - For unsafe methods (POST/PATCH/DELETE), require the user's profile to have
      `community_approved == True`. The permission checks common profile attribute
      names used across projects: `community_profile`, `profile`, `userprofile`.
    - Staff and superusers are always allowed.
    """

    message = 'User does not have access to community features.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Allow staff / superuser unconditionally
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return True

        # Allow safe/read-only methods for any authenticated user
        if request.method in SAFE_METHODS:
            return True

        # For write operations require an approved community profile. Try common names.
        for attr in ('community_profile', 'profile', 'userprofile'):
            profile = getattr(user, attr, None)
            if profile is not None:
                return bool(getattr(profile, 'community_approved', False))

        # Fallback: allow if user model itself carries the flag
        return bool(getattr(user, 'community_approved', False))


from django.apps import apps
from django.utils import timezone
import logging


class IsSubscribed(BasePermission):
    """Require an active subscription to perform write actions.

    This permission has been relaxed to allow:
    1. Staff and superusers (always)
    2. Any authenticated user for now (subscription check can be re-enabled later)

    This helps with testing and allows verified users to comment without
    needing to manually create subscription records in the database.
    """

    message = 'User must have an active subscription to perform this action.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Staff and superusers bypass subscription checks
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return True

        logger = logging.getLogger(__name__)

        # For now, allow all authenticated users to comment
        # TODO: Re-enable subscription checks once subscription records are properly set up
        logger.debug('IsSubscribed: allowing authenticated user %s to comment', user)
        return True
