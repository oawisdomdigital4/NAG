"""
Custom Django Admin Dashboard with Statistics Overview
Similar to: https://laravelui.spruko.com/ynex/index7
"""
from django.contrib import admin
from django.db.models import Count, Sum, Q
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, UserProfile
from community.models import Post, Comment, Group, GroupMembership
from courses.models import Course, Enrollment
from payments.models import Payment, Subscription
from promotions.models import EngagementLog
from summit.models import SummitHero


class AdminDashboardMixin:
    """Mixin to provide dashboard statistics to admin"""
    
    @staticmethod
    def get_dashboard_stats():
        """Calculate all dashboard statistics"""
        
        # Date ranges
        today = timezone.now().date()
        this_month = today.replace(day=1)
        last_30_days = timezone.now() - timedelta(days=30)
        
        # User Statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        facilitators = User.objects.filter(role='facilitator').count()
        corporate_users = User.objects.filter(role='corporate').count()
        individuals = User.objects.filter(role='individual').count()
        new_users = User.objects.filter(date_joined__gte=last_30_days).count()
        
        # User Profile Stats
        profiles_with_avatar = UserProfile.objects.filter(
            Q(avatar__isnull=False) | Q(avatar_url__isnull=False)
        ).exclude(Q(avatar='') & Q(avatar_url='')).count()
        verified_profiles = UserProfile.objects.filter(community_approved=True).count()
        
        # Community Statistics
        total_posts = Post.objects.count()
        total_comments = Comment.objects.count()
        total_groups = Group.objects.count()
        active_groups = Group.objects.annotate(
            member_count=Count('members')
        ).filter(member_count__gt=0).count()
        
        recent_posts = Post.objects.filter(created_at__gte=last_30_days).count()
        recent_comments = Comment.objects.filter(created_at__gte=last_30_days).count()
        
        # Course Statistics
        total_courses = Course.objects.count()
        published_courses = Course.objects.filter(is_published=True).count()
        total_enrollments = Enrollment.objects.count()
        active_enrollments = Enrollment.objects.filter(progress__gt=0).count()
        
        # Payment Statistics
        total_payments = Payment.objects.count()
        successful_payments = Payment.objects.filter(status='completed').count()
        total_revenue = Payment.objects.filter(
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Subscription Statistics
        active_subscriptions = Subscription.objects.filter(
            status__in=['active', 'trialing']
        ).count()
        
        # Engagement Statistics
        total_engagements = EngagementLog.objects.count() if EngagementLog.objects.exists() else 0
        
        # Followers
        total_followers = sum([
            UserProfile.objects.filter(user__followers_set__isnull=False)
            .distinct().count(),
        ])
        
        return {
            'user_stats': {
                'total_users': total_users,
                'active_users': active_users,
                'facilitators': facilitators,
                'corporate_users': corporate_users,
                'individuals': individuals,
                'new_users_30d': new_users,
                'profiles_with_avatar': profiles_with_avatar,
                'verified_profiles': verified_profiles,
                'total_followers': total_followers,
            },
            'community_stats': {
                'total_posts': total_posts,
                'total_comments': total_comments,
                'total_groups': total_groups,
                'active_groups': active_groups,
                'recent_posts_30d': recent_posts,
                'recent_comments_30d': recent_comments,
            },
            'course_stats': {
                'total_courses': total_courses,
                'published_courses': published_courses,
                'total_enrollments': total_enrollments,
                'active_enrollments': active_enrollments,
            },
            'payment_stats': {
                'total_payments': total_payments,
                'successful_payments': successful_payments,
                'total_revenue': float(total_revenue),
                'active_subscriptions': active_subscriptions,
            },
            'engagement_stats': {
                'total_engagements': total_engagements,
            }
        }
    
    @staticmethod
    def format_stat_box(label, value, icon, color, unit=''):
        """Format a statistics box with icon and color"""
        return {
            'label': label,
            'value': f"{value:,}" if isinstance(value, int) else f"{value:,.2f}",
            'unit': unit,
            'icon': icon,
            'color': color,
        }


def get_dashboard_cards():
    """Get formatted dashboard cards for template rendering"""
    stats = AdminDashboardMixin.get_dashboard_stats()
    
    cards = []
    
    # User Statistics Cards
    cards.append(AdminDashboardMixin.format_stat_box(
        'Total Users', stats['user_stats']['total_users'],
        'fas fa-users', 'primary', ''
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'Active Users', stats['user_stats']['active_users'],
        'fas fa-user-check', 'success', ''
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'Facilitators', stats['user_stats']['facilitators'],
        'fas fa-chalkboard-user', 'info', ''
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'New Users (30d)', stats['user_stats']['new_users_30d'],
        'fas fa-user-plus', 'warning', ''
    ))
    
    # Community Statistics Cards
    cards.append(AdminDashboardMixin.format_stat_box(
        'Total Posts', stats['community_stats']['total_posts'],
        'fas fa-sticky-note', 'danger', ''
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'Comments', stats['community_stats']['total_comments'],
        'fas fa-comments', 'secondary', ''
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'Groups', stats['community_stats']['total_groups'],
        'fas fa-layer-group', 'primary', ''
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'Active Groups', stats['community_stats']['active_groups'],
        'fas fa-check-circle', 'success', ''
    ))
    
    # Course Statistics Cards
    cards.append(AdminDashboardMixin.format_stat_box(
        'Total Courses', stats['course_stats']['total_courses'],
        'fas fa-book', 'info', ''
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'Published Courses', stats['course_stats']['published_courses'],
        'fas fa-check', 'success', ''
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'Enrollments', stats['course_stats']['total_enrollments'],
        'fas fa-user-graduate', 'warning', ''
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'Active Enrollments', stats['course_stats']['active_enrollments'],
        'fas fa-graduation-cap', 'success', ''
    ))
    
    # Payment Statistics Cards
    cards.append(AdminDashboardMixin.format_stat_box(
        'Total Payments', stats['payment_stats']['total_payments'],
        'fas fa-credit-card', 'danger', ''
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'Successful Payments', stats['payment_stats']['successful_payments'],
        'fas fa-check-circle', 'success', ''
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'Total Revenue', stats['payment_stats']['total_revenue'],
        'fas fa-money-bill', 'primary', '$'
    ))
    cards.append(AdminDashboardMixin.format_stat_box(
        'Active Subscriptions', stats['payment_stats']['active_subscriptions'],
        'fas fa-calendar-check', 'info', ''
    ))
    
    return cards
