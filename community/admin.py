from django.contrib import admin
from django.utils.html import format_html
from django import forms
import datetime
import json
from django.utils.safestring import mark_safe
from .models import (
    CommunitySection,
    CTABanner,
    # New models
    CorporateConnection,
    PartnerDirectory,
    WithdrawalRequest,
    UserEngagementScore,
    SubscriptionTier,
    SponsoredPost,
    TrendingTopic,
    CorporateOpportunity,
    OpportunityApplication,
    CollaborationRequest,
    PlatformAnalytics,
    # corporate verification model
    CorporateVerification,
)
from .models import GroupInvite
from .engagement import (
    CommunityEngagementLog,
    MentionLog,
    UserReputation,
    EngagementNotification,
)


@admin.register(CommunitySection)
class CommunitySectionAdmin(admin.ModelAdmin):
	list_display = ('id', 'title_main', 'title_highlight', 'is_published', 'created_at')
	readonly_fields = ('created_at', 'updated_at')
	fields = (
		'badge', 'title_main', 'title_highlight', 'description', 'image',
		# stats (explicit fields)
		'stat1_value', 'stat1_label', 'stat2_value', 'stat2_label', 'stat3_value', 'stat3_label',
		# cards (explicit fields)
		'card1_title', 'card1_description', 'card1_feature_1', 'card1_feature_2',
		'card2_title', 'card2_description', 'card2_feature_1', 'card2_feature_2',
		'cta_label', 'cta_url', 'is_published', 'created_at'
	)


@admin.action(description="Set subscription status to active")
def set_subscription_active(modeladmin, request, queryset):
	updated = queryset.update(status='active')
	modeladmin.message_user(request, f"Marked {updated} subscriptions active")


@admin.action(description="Set subscription status to cancelled")
def set_subscription_cancelled(modeladmin, request, queryset):
	updated = queryset.update(status='cancelled')
	modeladmin.message_user(request, f"Marked {updated} subscriptions cancelled")



@admin.register(CTABanner)
class CTABannerAdmin(admin.ModelAdmin):
	list_display = ('id', 'title_main', 'title_highlight', 'is_published', 'created_at')
	readonly_fields = ('created_at',)
	fields = (
		'badge', 'title_main', 'title_highlight', 'description',
		'primary_cta_label', 'primary_cta_url', 'secondary_cta_label', 'secondary_cta_url',
		'feature1_title', 'feature1_subtitle', 'feature2_title', 'feature2_subtitle', 'feature3_title', 'feature3_subtitle',
		'is_published', 'created_at'
	)



@admin.register(CorporateConnection)
class CorporateConnectionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('sender__username', 'receiver__username')


@admin.register(CorporateVerification)
class CorporateVerificationAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'status', 'submitted_at', 'reviewed_at')
    list_filter = ('status', 'submitted_at')
    search_fields = ('company_name', 'user__username', 'registration_number')
    readonly_fields = ('submitted_at', 'reviewed_at')
    fields = (
        'user', 'company_name', 'registration_number', 'official_website', 'industry',
        'contact_person_title', 'contact_phone', 'business_description',
        'status', 'review_reason', 'submitted_at', 'reviewed_at'
    )

    def save_model(self, request, obj, form, change):
        """Override save to timestamp reviews and notify the user when status changes."""
        from django.utils import timezone
        try:
            old_status = None
            if obj.pk:
                old_obj = type(obj).objects.get(pk=obj.pk)
                old_status = old_obj.status
        except Exception:
            old_status = None

        super().save_model(request, obj, form, change)

        # If status changed, record review time and notify the user
        try:
            if old_status != obj.status:
                obj.reviewed_at = timezone.now()
                obj.save(update_fields=['reviewed_at'])

                # Update user's community_approved status based on verification status
                if obj.user and obj.user.profile:
                    if obj.status == 'approved':
                        obj.user.profile.community_approved = True
                    elif obj.status in ['rejected', 'pending']:
                        obj.user.profile.community_approved = False
                    obj.user.profile.save()

                # send in-app notification to the corporate user
                try:
                    from notifications.utils import send_notification
                    if obj.user:
                        title = f"Verification {obj.status.capitalize()}"
                        message = f"Your verification status is now {obj.status}."
                        if obj.review_reason:
                            message = message + f" Reason: {obj.review_reason}"
                        send_notification(obj.user, 'corporate_verification', title, message, action_url='/dashboard/verification', metadata={'status': obj.status})
                except Exception:
                    # do not crash admin save if notifications fail
                    pass
        except Exception:
            pass


# CorporateOpportunity admin is registered below in the COMMUNITY SYSTEM ADMIN section
# (Old Opportunity model has been removed)

# PartnerDirectory admin commented out - using CorporateVerification directly
# @admin.register(PartnerDirectory)
# class PartnerDirectoryAdmin(admin.ModelAdmin):
#     list_display = ('company', 'get_website', 'created_at')
#     search_fields = ('company__username',)


# ============================================================================
# COMMUNITY SYSTEM ADMIN (NEW MODELS)
# ============================================================================

@admin.register(UserEngagementScore)
class UserEngagementScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'engagement_score', 'facilitator_authority_score', 'corporate_campaign_score', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'last_activity', 'updated_at')


@admin.register(SubscriptionTier)
class SubscriptionTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier_type', 'price', 'can_sponsor_posts', 'can_post_opportunities', 'priority_feed_ranking')
    list_filter = ('can_sponsor_posts', 'can_post_opportunities')
    fieldsets = (
        ('Basic Info', {
            'fields': ('tier_type', 'name', 'price', 'duration_days')
        }),
        ('Feature Permissions', {
            'fields': ('max_posts_per_day', 'can_create_groups', 'can_sponsor_posts', 
                      'can_post_opportunities', 'can_collaborate')
        }),
        ('Ranking', {
            'fields': ('priority_feed_ranking',)
        }),
    )


@admin.register(SponsoredPost)
class SponsoredPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'status', 'budget', 'spent', 'ctr', 'start_date')
    list_filter = ('status', 'start_date')
    search_fields = ('title', 'creator__username')
    readonly_fields = ('created_at', 'updated_at', 'ctr')
    fieldsets = (
        ('Basic Info', {
            'fields': ('creator', 'title', 'description', 'status')
        }),
        ('Budget & Metrics', {
            'fields': ('budget', 'daily_budget', 'spent', 'impressions', 'clicks', 'ctr')
        }),
        ('Campaign Details', {
            'fields': ('promotion_level', 'start_date', 'end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TrendingTopic)
class TrendingTopicAdmin(admin.ModelAdmin):
    list_display = ('topic', 'mention_count', 'engagement_score', 'last_mentioned')
    list_filter = ('created_at',)
    search_fields = ('topic',)
    readonly_fields = ('created_at',)


@admin.register(CorporateOpportunity)
class CorporateOpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'opportunity_type', 'status', 'view_count', 'application_count')
    list_filter = ('opportunity_type', 'status', 'remote_friendly')
    search_fields = ('title', 'creator__username')
    readonly_fields = ('view_count', 'application_count', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('creator', 'title', 'description', 'opportunity_type', 'status')
        }),
        ('Location & Details', {
            'fields': ('location', 'remote_friendly', 'start_date', 'deadline')
        }),
        ('Compensation', {
            'fields': ('salary_min', 'salary_max', 'salary_currency')
        }),
        ('Metrics', {
            'fields': ('view_count', 'application_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OpportunityApplication)
class OpportunityApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'opportunity', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('applicant__username', 'opportunity__title')
    readonly_fields = ('applied_at', 'status_updated_at')
    fieldsets = (
        ('Application Info', {
            'fields': ('applicant', 'opportunity', 'status')
        }),
        ('Application Details', {
            'fields': ('cover_letter', 'resume_url')
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'status_updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CollaborationRequest)
class CollaborationRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'recipient', 'collaboration_type', 'status', 'created_at')
    list_filter = ('collaboration_type', 'status', 'created_at')
    search_fields = ('requester__username', 'recipient__username', 'title')
    readonly_fields = ('created_at', 'responded_at')
    fieldsets = (
        ('Participants', {
            'fields': ('requester', 'recipient')
        }),
        ('Collaboration Info', {
            'fields': ('collaboration_type', 'title', 'description', 'status')
        }),
        ('Timeline', {
            'fields': ('proposed_start', 'proposed_end')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'responded_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PlatformAnalytics)
class PlatformAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_users', 'active_users_today', 'posts_created', 'subscriptions_active', 'mrr')
    list_filter = ('date',)
    readonly_fields = ('date',)
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Users', {
            'fields': ('total_users', 'active_users_today', 'new_users_today')
        }),
        ('Content', {
            'fields': ('posts_created', 'comments_created', 'likes_count', 'mentions_count')
        }),
        ('Monetization', {
            'fields': ('subscriptions_active', 'mrr')
        }),
    )


@admin.register(GroupInvite)
class GroupInviteAdmin(admin.ModelAdmin):
    list_display = ('group', 'invited_by', 'invited_user', 'invited_email', 'status', 'created_at', 'expires_at')
    list_filter = ('status', 'created_at')
    search_fields = ('invited_email', 'invited_user__username', 'invited_by__username')
    readonly_fields = ('token', 'created_at', 'accepted_at')


# ============================================================================
# ENGAGEMENT SYSTEM ADMIN
# ============================================================================

@admin.register(CommunityEngagementLog)
class CommunityEngagementLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'get_content_type', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('user__username', 'post__title', 'comment__content')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Engagement Details', {
            'fields': ('user', 'action_type', 'post', 'comment', 'group', 'mentioned_user')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_content_type(self, obj):
        """Display what was engaged with."""
        if obj.post:
            return f"Post: {obj.post.title[:50]}"
        elif obj.comment:
            return f"Comment: {obj.comment.content[:50]}"
        elif obj.group:
            return f"Group: {obj.group.name}"
        return "Unknown"
    get_content_type.short_description = "Content"


@admin.register(MentionLog)
class MentionLogAdmin(admin.ModelAdmin):
    list_display = ('mentioned_user', 'mentioned_by', 'get_mention_in', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('mentioned_user__username', 'mentioned_by__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Mention Details', {
            'fields': ('mentioned_user', 'mentioned_by', 'post', 'comment')
        }),
        ('Context', {
            'fields': ('mention_context',)
        }),
        ('Notification', {
            'fields': ('notification_sent',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_mention_in(self, obj):
        """Display where the mention occurred."""
        if obj.post:
            return f"Post: {obj.post.title[:50]}"
        elif obj.comment:
            return f"Comment: {obj.comment.content[:50]}"
        return "Unknown"
    get_mention_in.short_description = "Mentioned In"


@admin.register(UserReputation)
class UserReputationAdmin(admin.ModelAdmin):
    list_display = ('user', 'reputation_score', 'activity_level', 'created_at')
    list_filter = ('activity_level', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Reputation', {
            'fields': ('reputation_score', 'total_engagements', 'activity_level')
        }),
        ('Badges', {
            'fields': ('badges',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )


@admin.register(EngagementNotification)
class EngagementNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'read', 'email_sent', 'created_at')
    list_filter = ('notification_type', 'read', 'email_sent', 'created_at')
    search_fields = ('user__username', 'triggered_by__username', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'triggered_by', 'notification_type', 'message')
        }),
        ('Engagement Context', {
            'fields': ('engagement',)
        }),
        ('Delivery Status', {
            'fields': ('email_sent', 'email_delivered', 'in_app_sent', 'read')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
