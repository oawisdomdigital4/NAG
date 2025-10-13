from rest_framework import permissions


class IsFacilitator(permissions.BasePermission):
    """Allow access only to users whose `role` attribute is 'facilitator'."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Some user objects may store role on profile; handle both shapes
        role = getattr(user, 'role', None)
        if not role and hasattr(user, 'profile'):
            role = getattr(user.profile, 'role', None)
        return role == 'facilitator'


class IsCourseOwner(permissions.BasePermission):
    """Allow access only to the facilitator who owns the course instance."""

    def has_object_permission(self, request, view, obj):
        # obj is a Course instance
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return obj.facilitator_id == getattr(user, 'id', None)
