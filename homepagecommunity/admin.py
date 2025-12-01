from django.contrib import admin
from .models import (
    HeroSection, AboutCommunityMission, CommunityFeature,
    SubscriptionTier, SubscriptionBenefit, Testimonial,
    FinalCTA, CommunityMetrics
)


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Hero Title', {
            'fields': ('title_line_1', 'title_line_2', 'title_line_3', 'subtitle')
        }),
        ('Pricing Information', {
            'fields': (
                'individual_price', 'individual_period',
                'facilitator_price', 'facilitator_period',
                'corporate_price', 'corporate_period'
            )
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AboutCommunityMission)
class AboutCommunityMissionAdmin(admin.ModelAdmin):
    fields = ('mission_label', 'mission_title', 'mission_description', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CommunityFeature)
class CommunityFeatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'feature_type', 'order')
    list_editable = ('order',)
    list_filter = ('feature_type',)
    search_fields = ('title',)
    readonly_fields = ('created_at', 'updated_at')


class SubscriptionBenefitInline(admin.TabularInline):
    model = SubscriptionBenefit
    extra = 3
    fields = ('title', 'icon_name', 'order', 'description')


@admin.register(SubscriptionTier)
class SubscriptionTierAdmin(admin.ModelAdmin):
    list_display = ('tier_type', 'price', 'period')
    inlines = [SubscriptionBenefitInline]
    fieldsets = (
        ('Tier Information', {
            'fields': ('tier_type', 'title', 'subtitle', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'period')
        }),
        ('Styling', {
            'fields': ('label_color', 'bg_color', 'button_color')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SubscriptionBenefit)
class SubscriptionBenefitAdmin(admin.ModelAdmin):
    list_display = ('tier', 'title', 'order')
    list_editable = ('order',)
    list_filter = ('tier',)
    search_fields = ('title',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'title', 'quote')
    fields = ('name', 'title', 'quote', 'image', 'display_order', 'is_active', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FinalCTA)
class FinalCTAAdmin(admin.ModelAdmin):
    fields = (
        'title_part_1', 'title_teach', 'title_connect', 'title_empower',
        'subtitle', 'created_at', 'updated_at'
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CommunityMetrics)
class CommunityMetricsAdmin(admin.ModelAdmin):
    fields = (
        'total_members', 'active_groups', 'total_posts',
        'total_facilitators', 'total_courses', 'total_enrollments',
        'last_updated'
    )
    readonly_fields = ('last_updated',)
