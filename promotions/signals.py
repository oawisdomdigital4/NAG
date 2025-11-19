from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import SponsorCampaign


@receiver(post_save, sender=SponsorCampaign)
def invalidate_campaign_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalidate campaign-related caches when a campaign is saved.
    This ensures polling endpoints get fresh data.
    """
    # Invalidate active campaigns cache
    cache.delete('active_campaigns_metrics')
    
    # Invalidate user campaigns cache
    cache.delete(f'user_campaigns_metrics:{instance.sponsor_id}')
    
    # Invalidate trending campaigns cache
    cache.delete('trending_campaigns:10')
    cache.delete('trending_campaigns:5')
    
    # Update timestamp for polling detection
    instance.updated_at = __import__('django.utils.timezone', fromlist=['now']).now()
    if not created:
        SponsorCampaign.objects.filter(pk=instance.pk).update(
            updated_at=instance.updated_at
        )


@receiver(post_delete, sender=SponsorCampaign)
def invalidate_campaign_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate campaign caches when a campaign is deleted.
    """
    cache.delete('active_campaigns_metrics')
    cache.delete(f'user_campaigns_metrics:{instance.sponsor_id}')
    cache.delete('trending_campaigns:10')
    cache.delete('trending_campaigns:5')
