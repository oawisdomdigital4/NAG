"""
Views for custom admin dashboard
"""
from django.contrib.admin import AdminSite
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, UserProfile
from community.models import Post, Comment, Group
from courses.models import Course, Enrollment
from payments.models import Payment, Subscription


class DashboardMixin:
    """Mixin to add dashboard context to admin site"""
    
    def get_dashboard_context(self):
        """Get all dashboard statistics"""
        
        # Time ranges
        today = timezone.now().date()
        last_30_days = timezone.now() - timedelta(days=30)
        
        context = {
            # User Stats
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'facilitators': User.objects.filter(role='facilitator').count(),
            'corporate_users': User.objects.filter(role='corporate').count(),
            'individuals': User.objects.filter(role='individual').count(),
            'new_users_month': User.objects.filter(date_joined__gte=last_30_days).count(),
            'verified_profiles': UserProfile.objects.filter(community_approved=True).count(),
            
            # Community Stats
            'total_posts': Post.objects.count(),
            'total_comments': Comment.objects.count(),
            'total_groups': Group.objects.count(),
            'posts_month': Post.objects.filter(created_at__gte=last_30_days).count(),
            
            # Course Stats
            'total_courses': Course.objects.count(),
            'published_courses': Course.objects.filter(is_published=True).count(),
            'total_enrollments': Enrollment.objects.count(),
            'active_enrollments': Enrollment.objects.filter(progress__gt=0).count(),
            
            # Payment Stats
            'total_payments': Payment.objects.count(),
            'successful_payments': Payment.objects.filter(status='completed').count(),
            'total_revenue': Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
            'active_subscriptions': Subscription.objects.filter(status__in=['active', 'trialing']).count(),
        }
        
        return context

    def index(self, request, extra_context=None):
        """Override index to add dashboard stats"""
        extra_context = extra_context or {}
        extra_context.update(self.get_dashboard_context())
        return super().index(request, extra_context)


# Create custom admin site
class CustomAdminSite(DashboardMixin, AdminSite):
    site_header = "The New Africa Group - Platform Admin"
    site_title = "NAG Admin"
    index_title = "Dashboard Overview"
    
    def has_permission(self, request):
        """Check if user has admin permission"""
        return request.user.is_active and (request.user.is_staff or request.user.is_superuser)
