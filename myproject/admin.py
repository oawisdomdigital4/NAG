"""
Admin configuration with enhanced dashboard stats
"""
from django.contrib import admin
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
import json

# Import models inside try block to avoid circular imports
from accounts.models import User, UserProfile
from community.models import Post, Comment, Group
from courses.models import Course, Enrollment
from payments.models import Payment, Subscription


class EnhancedAdminSite(admin.AdminSite):
    """Enhanced admin site with live statistics dashboard"""
    site_header = "NAG Platform Administration"
    site_title = "NAG Admin"
    index_title = "Platform Dashboard"
    
    def index(self, request, extra_context=None):
        """Override admin index to inject live statistics"""
        extra_context = extra_context or {}
        
        try:
            # User Statistics
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            facilitators = User.objects.filter(role='facilitator').count()
            corporate_users = User.objects.filter(role='corporate').count()
            new_users_30days = User.objects.filter(
                date_joined__gte=timezone.now() - timedelta(days=30)
            ).count()
            
            # Community Statistics
            total_posts = Post.objects.count()
            total_comments = Comment.objects.count()
            total_groups = Group.objects.count()
            posts_30days = Post.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()
            engagement_rate = round(
                (total_posts + total_comments) / max(active_users, 1) * 100, 1
            ) if active_users > 0 else 0
            
            # Course Statistics
            total_courses = Course.objects.count()
            published_courses = Course.objects.filter(is_published=True).count()
            total_enrollments = Enrollment.objects.count()
            active_enrollments = Enrollment.objects.filter(progress__gt=0, progress__lt=100).count()
            completed_enrollments = Enrollment.objects.filter(progress=100).count()
            completion_rate = round(
                (completed_enrollments / max(total_enrollments, 1)) * 100, 1
            ) if total_enrollments > 0 else 0
            
            # Payment & Revenue Statistics
            total_transactions = Payment.objects.count()
            successful_transactions = Payment.objects.filter(status='completed').count()
            failed_transactions = Payment.objects.filter(status='failed').count()
            total_revenue = Payment.objects.filter(
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            revenue_30days = Payment.objects.filter(
                status='completed',
                created_at__gte=timezone.now() - timedelta(days=30)
            ).aggregate(total=Sum('amount'))['total'] or 0
            active_subscriptions = Subscription.objects.filter(status='active').count()
            
            # User Growth - Last 30 Days
            user_growth_data = []
            for i in range(30, -1, -1):
                date = timezone.now() - timedelta(days=i)
                date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = date_start + timedelta(days=1)
                
                count = User.objects.filter(
                    date_joined__gte=date_start,
                    date_joined__lt=date_end
                ).count()
                
                user_growth_data.append({
                    'date': date.strftime('%m/%d'),
                    'users': count
                })
            
            # Revenue Trend - Last 30 Days
            revenue_trend_data = []
            for i in range(30, -1, -1):
                date = timezone.now() - timedelta(days=i)
                date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = date_start + timedelta(days=1)
                
                revenue = Payment.objects.filter(
                    status='completed',
                    created_at__gte=date_start,
                    created_at__lt=date_end
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                revenue_trend_data.append({
                    'date': date.strftime('%m/%d'),
                    'revenue': float(revenue)
                })
            
            # Top Courses by Enrollment
            top_courses = Course.objects.annotate(
                enrollment_count=Count('enrollments')
            ).order_by('-enrollment_count')[:5]
            
            top_courses_data = [
                {'name': course.title[:20], 'enrollments': course.enrollment_count}
                for course in top_courses
            ]
            
            # Conversion data
            subscription_revenue = Subscription.objects.filter(
                status='active'
            ).aggregate(total=Sum('plan__price'))['total'] or 0
            
            # Add all stats to context
            extra_context.update({
                # User Stats
                'total_users': total_users,
                'active_users': active_users,
                'facilitators': facilitators,
                'corporate_users': corporate_users,
                'new_users_30days': new_users_30days,
                
                # Community Stats
                'total_posts': total_posts,
                'total_comments': total_comments,
                'total_groups': total_groups,
                'posts_30days': posts_30days,
                'engagement_rate': engagement_rate,
                
                # Course Stats
                'total_courses': total_courses,
                'published_courses': published_courses,
                'total_enrollments': total_enrollments,
                'active_enrollments': active_enrollments,
                'completed_enrollments': completed_enrollments,
                'completion_rate': completion_rate,
                
                # Payment Stats
                'total_transactions': total_transactions,
                'successful_transactions': successful_transactions,
                'failed_transactions': failed_transactions,
                'total_revenue': float(total_revenue),
                'revenue_30days': float(revenue_30days),
                'active_subscriptions': active_subscriptions,
                'subscription_revenue': float(subscription_revenue),
                
                # Chart Data (JSON)
                'user_growth_data': json.dumps(user_growth_data),
                'revenue_trend_data': json.dumps(revenue_trend_data),
                'top_courses_data': json.dumps(top_courses_data),
            })
            
        except Exception as e:
            print(f"Error loading dashboard stats: {e}")
            import traceback
            traceback.print_exc()
            # Provide defaults if error
            extra_context.update({
                'total_users': 0, 'active_users': 0, 'facilitators': 0,
                'corporate_users': 0, 'new_users_30days': 0,
                'total_posts': 0, 'total_comments': 0, 'total_groups': 0,
                'posts_30days': 0, 'engagement_rate': 0,
                'total_courses': 0, 'published_courses': 0,
                'total_enrollments': 0, 'active_enrollments': 0,
                'completed_enrollments': 0, 'completion_rate': 0,
                'total_transactions': 0, 'successful_transactions': 0,
                'failed_transactions': 0, 'total_revenue': 0, 'revenue_30days': 0,
                'active_subscriptions': 0, 'subscription_revenue': 0,
                'user_growth_data': '[]', 'revenue_trend_data': '[]',
                'top_courses_data': '[]',
            })
        
        return super().index(request, extra_context)


# Replace the default admin site's class with our enhanced one
admin.site.__class__ = EnhancedAdminSite
# Also update its class attributes
admin.site.site_header = "NAG Platform Administration"
admin.site.site_title = "NAG Admin"
admin.site.index_title = "Platform Dashboard"

# Export for use in URLs
admin_site = admin.site
