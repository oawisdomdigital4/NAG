from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from enum import Enum
from django.db.models import Q

class UserRole(Enum):
    INDIVIDUAL = 'individual'
    FACILITATOR = 'facilitator'
    CORPORATE = 'corporate'
    ADMIN = 'admin'

    @classmethod
    def choices(cls):
        return [(role.value, role.name.title()) for role in cls]

    @staticmethod
    def get_role_permissions(role):
        """Get permissions for a specific role."""
        if role == UserRole.INDIVIDUAL.value:
            return {
                'can_comment': True,
                'can_like': True,
                'can_join_groups': True,
                'can_apply_jobs': True,
                'can_view_content': True,
            }
        elif role == UserRole.FACILITATOR.value:
            return {
                **UserRole.get_role_permissions(UserRole.INDIVIDUAL.value),
                'can_create_groups': True,
                'can_sponsor_content': True,
                'can_access_analytics': True,
                'can_post_updates': True,
            }
        elif role == UserRole.CORPORATE.value:
            return {
                **UserRole.get_role_permissions(UserRole.INDIVIDUAL.value),
                'can_create_corporate_groups': True,
                'can_post_jobs': True,
                'can_sponsor_content': True,
                'can_access_analytics': True,
                'can_create_collaborations': True,
            }
        elif role == UserRole.ADMIN.value:
            return {
                **UserRole.get_role_permissions(UserRole.CORPORATE.value),
                'can_manage_users': True,
                'can_manage_content': True,
                'can_manage_subscriptions': True,
                'can_access_admin': True,
            }
        return {}

class RoleManager:
    """Manages role-based permissions and access control."""
    
    @staticmethod
    def sync_role_permissions():
        """Create and sync permissions for all roles."""
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from community.models import Post, Group, Comment, SponsorCampaign

        # Create role groups if they don't exist
        for role in UserRole:
            group, _ = Group.objects.get_or_create(name=role.value)
            
            # Get role permissions
            role_perms = UserRole.get_role_permissions(role.value)
            
            # Map permission codenames to actual permissions
            permission_mapping = {
                'can_comment': ['add_comment', 'change_comment', 'delete_comment'],
                'can_like': ['add_postreaction', 'delete_postreaction'],
                'can_join_groups': ['add_groupmembership', 'delete_groupmembership'],
                'can_create_groups': ['add_group', 'change_group'],
                'can_sponsor_content': ['add_sponsorcampaign', 'change_sponsorcampaign'],
                'can_access_analytics': ['view_engagementlog'],
                'can_post_updates': ['add_post', 'change_post', 'delete_post'],
                'can_post_jobs': ['add_job', 'change_job', 'delete_job'],
                'can_manage_users': ['add_user', 'change_user', 'delete_user'],
                'can_manage_content': ['change_post', 'delete_post', 'change_comment', 'delete_comment'],
                'can_manage_subscriptions': ['change_subscription', 'delete_subscription'],
            }

            # Get all content types
            content_types = ContentType.objects.get_for_models(
                Post, Group, Comment, SponsorCampaign
            )

            # Collect permissions for this role
            role_permissions = []
            for perm_name, enabled in role_perms.items():
                if not enabled:
                    continue
                    
                # Get mapped permission codenames
                codenames = permission_mapping.get(perm_name, [])
                for codename in codenames:
                    # Try to find the right content type and permission
                    for ct in content_types.values():
                        try:
                            perm = Permission.objects.get(
                                codename=codename,
                                content_type=ct
                            )
                            role_permissions.append(perm)
                        except Permission.DoesNotExist:
                            continue

            # Set group permissions
            group.permissions.set(role_permissions)

    @staticmethod
    def assign_role(user, role):
        """Assign a role to a user."""
        from django.contrib.auth.models import Group
        
        # Remove existing roles
        user.groups.filter(name__in=[r.value for r in UserRole]).delete()
        
        # Add new role
        group, _ = Group.objects.get_or_create(name=role.value)
        user.groups.add(group)
        
        # Update profile
        if hasattr(user, 'community_profile'):
            user.community_profile.role = role.value
            user.community_profile.save()

    @staticmethod
    def get_user_role(user):
        """Get a user's current role."""
        if not user.is_authenticated:
            return None
            
        # Check groups first
        role_group = user.groups.filter(
            name__in=[r.value for r in UserRole]
        ).first()
        
        if role_group:
            return role_group.name
            
        # Fallback to profile
        if hasattr(user, 'community_profile'):
            return user.community_profile.role
            
        return None

    @staticmethod
    def check_role_permission(user, permission):
        """Check if user's role has a specific permission."""
        role = RoleManager.get_user_role(user)
        if not role:
            return False
            
        role_perms = UserRole.get_role_permissions(role)
        return role_perms.get(permission, False)