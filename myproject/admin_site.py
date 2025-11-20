"""
Custom Django Admin Site with Dashboard
"""
from django.contrib import admin
from myproject.admin_dashboard import AdminDashboardMixin


class CustomAdminSite(admin.AdminSite):
    """Custom Admin Site with Dashboard Statistics"""
    
    site_header = "The New Africa Group - Admin Panel"
    site_title = "NAG Admin"
    index_title = "Platform Dashboard"
    
    def index(self, request, extra_context=None):
        """Override admin index to show custom dashboard"""
        
        # Get statistics
        stats = AdminDashboardMixin.get_dashboard_stats()
        
        extra_context = extra_context or {}
        extra_context.update({
            'user_stats': stats['user_stats'],
            'community_stats': stats['community_stats'],
            'course_stats': stats['course_stats'],
            'payment_stats': stats['payment_stats'],
            'engagement_stats': stats['engagement_stats'],
        })
        
        return super().index(request, extra_context)


# Create instance of custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')
