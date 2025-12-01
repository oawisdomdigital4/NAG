from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from django.core.files.storage import default_storage
from django.conf import settings
import os
from .models import (
    SponsorCampaign,
    CampaignAnalytics,
    PromotionMetrics,
    WithdrawalRequest,
    FacilitatorEarning,
    WalletTopUp,
)


class SponsorCampaignForm(forms.ModelForm):
    """Custom form for SponsorCampaign with image upload"""
    upload_image = forms.ImageField(
        required=False,
        help_text='Upload a new image to add to campaign media URLs'
    )
    
    class Meta:
        model = SponsorCampaign
        fields = '__all__'


@admin.register(SponsorCampaign)
class SponsorCampaignAdmin(admin.ModelAdmin):
    form = SponsorCampaignForm
    list_display = ('icon', 'title', 'sponsor', 'status', 'start_date', 'end_date', 'budget', 'campaign_image_preview', 'created_at')
    list_filter = ('status', 'priority_level', 'created_at')
    search_fields = ('title', 'sponsor__username', 'sponsor__email')
    readonly_fields = ('created_at', 'updated_at', 'impression_count', 'click_count', 'campaign_image_display', 'sponsored_post_link', 'current_media_urls', 'edit_media_urls')
    actions = ['mark_active', 'mark_rejected', 'mark_under_review']
    fieldsets = (
        ('Campaign Information', {
            'fields': ('title', 'description', 'sponsor', 'sponsored_post', 'sponsored_post_link')
        }),
        ('Campaign Media', {
            'fields': ('campaign_image_display', 'current_media_urls', 'edit_media_urls', 'upload_image'),
            'description': 'View and manage campaign images. Upload new images or view current media URLs.',
            'classes': ()
        }),
        ('Campaign Dates & Duration', {
            'fields': ('start_date', 'end_date')
        }),
        ('Campaign Performance', {
            'fields': ('status', 'priority_level', 'impression_count', 'click_count', 'engagement_rate'),
            'classes': ('collapse',)
        }),
        ('Budget & Pricing', {
            'fields': ('budget', 'cost_per_view')
        }),
        ('Targeting & Audience', {
            'fields': ('target_audience',)
        }),
        ('Payment Information', {
            'fields': ('payment_id', 'payment_status'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def campaign_image_preview(self, obj):
        """Display thumbnail in list view"""
        try:
            if obj.sponsored_post and hasattr(obj.sponsored_post, 'media_urls') and obj.sponsored_post.media_urls:
                if isinstance(obj.sponsored_post.media_urls, list) and len(obj.sponsored_post.media_urls) > 0:
                    image_url = obj.sponsored_post.media_urls[0]
                elif isinstance(obj.sponsored_post.media_urls, str):
                    image_url = obj.sponsored_post.media_urls
                else:
                    return format_html('<span style="color: #999;">Invalid image</span>')
                return format_html(
                    '<img src="{}" width="50" height="50" style="border-radius: 4px; object-fit: cover;" />', 
                    image_url
                )
        except Exception:
            pass
        return format_html('<span style="color: #999;">No image</span>')
    campaign_image_preview.short_description = 'Campaign Image'

    def icon(self, obj):
        return format_html("<i class='fas fa-bullhorn' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''

    def campaign_image_display(self, obj):
        """Display larger preview in detail view"""
        try:
            if obj.sponsored_post and hasattr(obj.sponsored_post, 'media_urls') and obj.sponsored_post.media_urls:
                if isinstance(obj.sponsored_post.media_urls, list) and len(obj.sponsored_post.media_urls) > 0:
                    image_url = obj.sponsored_post.media_urls[0]
                elif isinstance(obj.sponsored_post.media_urls, str):
                    image_url = obj.sponsored_post.media_urls
                else:
                    return format_html('<span style="color: #999;">Invalid image format</span>')
                return format_html(
                    '<div style="max-width: 300px;">'
                    '<img src="{}" style="max-width: 100%; height: auto; border-radius: 8px; border: 2px solid #ddd; padding: 8px;" />'
                    '<p style="margin-top: 8px; font-size: 12px; color: #666;">Featured image preview</p>'
                    '</div>',
                    image_url
                )
        except Exception:
            pass
        return format_html('<span style="color: #999;">No image attached.</span>')
    campaign_image_display.short_description = 'Campaign Featured Image'

    def current_media_urls(self, obj):
        """Display current media URLs"""
        if obj.sponsored_post and hasattr(obj.sponsored_post, 'media_urls'):
            media_urls = obj.sponsored_post.media_urls
            if isinstance(media_urls, list):
                if len(media_urls) == 0:
                    return format_html('<span style="color: #999;">No media URLs</span>')
                html = '<ul style="list-style-type: none; padding: 0;">'
                for url in media_urls:
                    html += f'<li style="padding: 4px 0;"><a href="{url}" target="_blank" style="color: #0066cc; word-break: break-all;">{url[:60]}...</a></li>'
                html += '</ul>'
                return format_html(html)
            elif isinstance(media_urls, str):
                return format_html('<a href="{}" target="_blank" style="color: #0066cc; word-break: break-all;">{}</a>', media_urls, media_urls[:80] + '...' if len(media_urls) > 80 else media_urls)
        return format_html('<span style="color: #999;">No media URLs</span>')
    current_media_urls.short_description = 'Current Media URLs'

    def edit_media_urls(self, obj):
        """Display editable media URLs as readonly with instructions"""
        if not obj or not obj.sponsored_post:
            return format_html('<span style="color: #999;">No post linked</span>')
        
        media_urls = obj.sponsored_post.media_urls
        urls_text = ''
        
        if isinstance(media_urls, list):
            urls_text = '\n'.join(media_urls)
        elif isinstance(media_urls, str):
            urls_text = media_urls
        
        # Display as readonly textarea with save instructions
        return format_html(
            '<textarea readonly style="width: 100%; height: 150px; font-family: monospace; padding: 8px; border: 1px solid #ccc; border-radius: 4px; background-color: #f9f9f9;">{}</textarea>'
            '<p style="margin-top: 8px; font-size: 12px; color: #666;">'
            '<strong>To edit media URLs:</strong> Use the "Manage Campaign Media" button below or edit the associated post directly. Then refresh this page to see changes.'
            '</p>',
            urls_text
        )
    edit_media_urls.short_description = 'Current Media URLs (Read-only)'

    def sponsored_post_link(self, obj):
        """Display link to the sponsored post"""
        if obj.sponsored_post:
            try:
                url = reverse('admin:community_post_change', args=[obj.sponsored_post.id])
                return format_html(
                    '<a href="{}" target="_blank">View Post #{} - "{}" in admin</a>',
                    url,
                    obj.sponsored_post.id,
                    obj.sponsored_post.title[:50]
                )
            except:
                # If the URL can't be reversed, just show the post info
                return format_html(
                    'Post #{} - <strong>{}</strong><br/><small style="color: #666;">Post ID in database</small>',
                    obj.sponsored_post.id,
                    obj.sponsored_post.title[:50]
                )
        return format_html('<span style="color: #999;">No post linked</span>')
    sponsored_post_link.short_description = 'Associated Post'

    def save_model(self, request, obj, form, change):
        """Override save to handle campaign updates and image uploads"""
        super().save_model(request, obj, form, change)
        
        # Handle image upload
        if obj.sponsored_post and form.cleaned_data.get('upload_image'):
            uploaded_file = form.cleaned_data['upload_image']
            
            try:
                # Save the uploaded file to media storage
                file_name = f"campaigns/{obj.id}/{uploaded_file.name}"
                file_path = default_storage.save(file_name, uploaded_file)
                file_url = default_storage.url(file_path)
                
                # Replace media_urls with new image (keep as list with single item)
                obj.sponsored_post.media_urls = [file_url]
                obj.sponsored_post.save(update_fields=['media_urls'])
                
                self.message_user(
                    request,
                    f'✓ Image uploaded successfully! Campaign image updated.',
                    level='success'
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'⚠ Error uploading image: {str(e)}',
                    level='warning'
                )

    def mark_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f"Marked {updated} campaign(s) as active")
    mark_active.short_description = 'Mark selected campaigns as Active'

    def mark_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"Marked {updated} campaign(s) as Rejected")
    mark_rejected.short_description = 'Mark selected campaigns as Rejected'

    def mark_under_review(self, request, queryset):
        updated = queryset.update(status='under_review')
        self.message_user(request, f"Marked {updated} campaign(s) as Under Review")
    mark_under_review.short_description = 'Mark selected campaigns as Under Review'


@admin.register(CampaignAnalytics)
class CampaignAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('icon', 'campaign', 'date', 'impressions', 'clicks', 'conversions', 'spend')
    list_filter = ('date', 'campaign')
    search_fields = ('campaign__title',)
    date_hierarchy = 'date'

    def icon(self, obj):
        return format_html("<i class='fas fa-chart-line' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''


@admin.register(PromotionMetrics)
class PromotionMetricsAdmin(admin.ModelAdmin):
    list_display = (
        'icon',
        'campaign',
        'date',
        'impressions',
        'clicks',
        'conversions',
        'engagement_rate',
        'spend',
        'roi'
    )
    list_filter = ('date', 'campaign')
    search_fields = ('campaign__title',)
    readonly_fields = (
        'engagement_rate',
        'conversion_rate',
        'cpc',
        'cpm',
        'roi'
    )
    date_hierarchy = 'date'

    def icon(self, obj):
        return format_html("<i class='fas fa-chart-bar' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # If the PromotionMetrics model exposes a calculate_metrics helper, call it
        if hasattr(obj, 'calculate_metrics'):
            try:
                obj.calculate_metrics()
            except Exception:
                # don't block admin save if metric calculation fails
                pass


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('icon', 'facilitator', 'amount', 'status', 'requested_at', 'processed_at')
    list_filter = ('status', 'requested_at', 'processed_at')
    search_fields = ('facilitator__username', 'bank_name', 'account_name')
    readonly_fields = ('requested_at', 'processed_at', 'processed_by')
    fields = ('facilitator', 'amount', 'status', 'bank_name', 'account_number', 'account_name', 'notes', 'requested_at', 'processed_at', 'processed_by')
    date_hierarchy = 'requested_at'

    def icon(self, obj):
        return format_html("<i class='fas fa-money-bill-wave' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''

    def save_model(self, request, obj, form, change):
        import logging
        logger = logging.getLogger(__name__)
        
        # Always check if we need to process the withdrawal
        if change:  # Only on update, not create
            try:
                old_obj = WithdrawalRequest.objects.get(pk=obj.pk)
                old_status = old_obj.status
                new_status = obj.status
                
                logger.info(f"Withdrawal {obj.pk}: status changing from {old_status} to {new_status}")
                
                # If transitioning to approved or completed, process the withdrawal
                if new_status in ['approved', 'completed'] and old_status != new_status:
                    logger.info(f"Processing withdrawal {obj.pk} for status {new_status}")
                    obj.process(new_status, request.user, obj.notes or '')
                    logger.info(f"Withdrawal {obj.pk} processed successfully")
                    return  # process() already saves, don't call super().save_model
                else:
                    logger.info(f"No processing needed for withdrawal {obj.pk}")
            except WithdrawalRequest.DoesNotExist:
                logger.error(f"Withdrawal {obj.pk} not found for update")
            except Exception as e:
                logger.error(f"Error processing withdrawal {obj.pk}: {str(e)}", exc_info=True)
                # Fall through to normal save on error
        
        # Normal save for other cases (create or no status change)
        super().save_model(request, obj, form, change)


@admin.register(FacilitatorEarning)
class FacilitatorEarningAdmin(admin.ModelAdmin):
    list_display = ('icon', 'facilitator', 'amount', 'source', 'earned_at', 'is_paid')
    list_filter = ('is_paid', 'source', 'earned_at')
    search_fields = ('facilitator__username', 'description')
    date_hierarchy = 'earned_at'

    def icon(self, obj):
        return format_html("<i class='fas fa-dollar-sign' style='font-size:14px;color:#0D1B52;'></i>")
    icon.short_description = ''


@admin.register(WalletTopUp)
class WalletTopUpAdmin(admin.ModelAdmin):
    list_display = ('icon', 'user', 'amount', 'status', 'payment_method', 'created_at', 'completed_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'user__email', 'transaction_id')
    readonly_fields = ('user', 'transaction_id', 'created_at', 'updated_at')
    actions = ['mark_completed', 'mark_failed']
    fieldsets = (
        ('Top-Up Information', {
            'fields': ('user', 'amount', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'transaction_id', 'payment_reference')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'

    def icon(self, obj):
        status_colors = {
            'completed': '#10b981',
            'processing': '#f59e0b',
            'pending': '#6b7280',
            'failed': '#ef4444',
            'cancelled': '#9ca3af',
        }
        color = status_colors.get(obj.status, '#6b7280')
        return format_html(f"<i class='fas fa-wallet' style='font-size:14px;color:{color};'></i>")
    icon.short_description = ''

    def mark_completed(self, request, queryset):
        """Mark selected top-ups as completed and add funds to wallets"""
        count = 0
        for topup in queryset.filter(status__in=['pending', 'processing']):
            try:
                topup.mark_completed()
                count += 1
            except Exception as e:
                self.message_user(request, f'Error completing {topup.id}: {str(e)}', level='error')
        self.message_user(request, f'{count} wallet top-ups completed successfully.')
    mark_completed.short_description = "Mark selected as completed and add funds to wallets"

    def mark_failed(self, request, queryset):
        """Mark selected top-ups as failed"""
        count = queryset.filter(status__in=['pending', 'processing']).update(status='failed')
        self.message_user(request, f'{count} wallet top-ups marked as failed.')
    mark_failed.short_description = "Mark selected as failed"


