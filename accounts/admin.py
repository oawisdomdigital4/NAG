from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    User,
    UserProfile,
    UserToken,
)
from django.utils.html import format_html
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin as DefaultGroupAdmin


# -----------------------------
# Custom UserAdmin
# -----------------------------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("icon", "email", "username", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "username")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "role", "subscription_status", "subscription_type")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2", "role", "is_active", "is_staff"),
        }),
    )

    def icon(self, obj):
        # Show user avatar if exists on related profile, otherwise a Font Awesome user icon
        try:
            profile = getattr(obj, 'profile', None) or getattr(obj, 'userprofile', None)
            if profile:
                avatar = getattr(profile, 'avatar', None) or getattr(profile, 'avatar_url', None)
                if avatar:
                    # avatar may be a FieldFile or a URL string
                    url = avatar.url if hasattr(avatar, 'url') else avatar
                    return format_html("<img src='{}' style='max-height:32px; border-radius:6px' />", url)
        except Exception:
            pass
        return format_html("<i class='fas fa-user-circle' style='font-size:18px;color:#0D1B52;'></i>")
    icon.short_description = ''


# -----------------------------
# UserProfile Admin
# -----------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "phone", "country", "company_name", "community_approved", "has_avatar")
    search_fields = ("user__email", "full_name", "phone", "country", "company_name")
    actions = ("approve_community_access", "revoke_community_access")
    readonly_fields = ("avatar_preview",)

    def avatar_preview(self, obj):
        if obj.avatar:
            return f"<img src='{obj.avatar.url}' style='max-height:50px' />"
        if obj.avatar_url:
            return f"<img src='{obj.avatar_url}' style='max-height:50px' />"
        return "-"
    avatar_preview.allow_tags = True
    avatar_preview.short_description = "Avatar"

    def has_avatar(self, obj):
        return bool(obj.avatar or obj.avatar_url)
    has_avatar.boolean = True
    has_avatar.short_description = "Has Avatar?"

    @admin.action(description="Approve community access")
    def approve_community_access(self, request, queryset):
        updated = queryset.update(community_approved=True)
        self.message_user(request, f"Approved community access for {updated} profiles")

    @admin.action(description="Revoke community access")
    def revoke_community_access(self, request, queryset):
        updated = queryset.update(community_approved=False)
        self.message_user(request, f"Revoked community access for {updated} profiles")


# -----------------------------
# UserToken Admin
# -----------------------------
@admin.register(UserToken)
class UserTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at", "expires_at", "is_expired")
    search_fields = ("user__email", "token")
    readonly_fields = ("token", "created_at", "expires_at")

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = "Expired?"


# Unregister default Group admin and re-register with an icon column
try:
    admin.site.unregister(Group)
except Exception:
    pass


@admin.register(Group)
class GroupAdmin(DefaultGroupAdmin):
    list_display = ("icon",) + DefaultGroupAdmin.list_display

    def icon(self, obj):
        return format_html("<i class='fas fa-users' style='font-size:16px;color:#0D1B52;'></i>")
    icon.short_description = ''
