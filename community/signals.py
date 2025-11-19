from django.dispatch import receiver
from django.db.models.signals import post_save
from accounts.models import UserProfile

from payments.models import Subscription
from .models import CollaborationRequest

@receiver(post_save, sender=Subscription)
def handle_subscription_change(sender, instance, created, **kwargs):
    """Set community_approved on the user's profile when subscription becomes active.

    This handler marks profile.community_approved = True when Subscription.status == 'active'
    and marks False when subscription is cancelled/expired.
    """
    try:
        profile = UserProfile.objects.get(user=instance.user)
    except UserProfile.DoesNotExist:
        # No profile to update
        return

    if instance.status == 'active':
        profile.community_approved = True
        profile.save()
    else:
        # For other statuses, revoke community access
        profile.community_approved = False
        profile.save()


@receiver(post_save, sender=CollaborationRequest)
def send_collaboration_notification(sender, instance, created, **kwargs):
    """Send notifications for collaboration requests with perspective-aware messages."""
    import logging
    logger = logging.getLogger(__name__)
    
    if not created:
        # Handle status changes (accepted/declined)
        if instance.status == 'accepted':
            try:
                from notifications.utils import send_notification
                recipient_name = getattr(instance.recipient, 'username', str(instance.recipient))
                requester_name = getattr(instance.requester, 'username', str(instance.requester))
                
                # Notification to requester: "X accepted your partnership request"
                send_notification(
                    instance.requester,
                    'collaboration_accepted',
                    f"{recipient_name} accepted your {instance.collaboration_type} request",
                    f"{recipient_name} has accepted your {instance.collaboration_type} collaboration request about '{instance.title}'",
                    action_url=f"/dashboard/community/collaborations/{instance.id}/",
                    metadata={'collaboration_request_id': instance.id, 'recipient_id': instance.recipient.id}
                )
                
                # Notification to recipient: "You accepted X's partnership request"
                send_notification(
                    instance.recipient,
                    'collaboration_accepted',
                    f"You accepted {requester_name}'s {instance.collaboration_type} request",
                    f"You have accepted {requester_name}'s {instance.collaboration_type} collaboration request about '{instance.title}'",
                    action_url=f"/dashboard/community/collaborations/{instance.id}/",
                    metadata={'collaboration_request_id': instance.id, 'requester_id': instance.requester.id}
                )
            except Exception as e:
                logger.warning(f"Failed to send collaboration acceptance notification: {e}")
        
        elif instance.status == 'declined':
            try:
                from notifications.utils import send_notification
                recipient_name = getattr(instance.recipient, 'username', str(instance.recipient))
                requester_name = getattr(instance.requester, 'username', str(instance.requester))
                
                # Notification to requester: "X declined your partnership request"
                send_notification(
                    instance.requester,
                    'collaboration_declined',
                    f"{recipient_name} declined your {instance.collaboration_type} request",
                    f"{recipient_name} has declined your {instance.collaboration_type} collaboration request about '{instance.title}'",
                    action_url=f"/dashboard/community/collaborations/{instance.id}/",
                    metadata={'collaboration_request_id': instance.id, 'recipient_id': instance.recipient.id}
                )
                
                # Notification to recipient: "You declined X's partnership request"
                send_notification(
                    instance.recipient,
                    'collaboration_declined',
                    f"You declined {requester_name}'s {instance.collaboration_type} request",
                    f"You have declined {requester_name}'s {instance.collaboration_type} collaboration request about '{instance.title}'",
                    action_url=f"/dashboard/community/collaborations/{instance.id}/",
                    metadata={'collaboration_request_id': instance.id, 'requester_id': instance.requester.id}
                )
            except Exception as e:
                logger.warning(f"Failed to send collaboration decline notification: {e}")
        return
    
    # On creation: send notification to recipient
    try:
        from notifications.utils import send_notification
        
        requester_name = getattr(instance.requester, 'username', str(instance.requester))
        recipient_name = getattr(instance.recipient, 'username', str(instance.recipient))
        
        # Notification to recipient: "X wants to collaborate with you on..."
        recipient_title = f"New {instance.collaboration_type} request from {requester_name}"
        recipient_message = f"{requester_name} wants to collaborate with you on a {instance.collaboration_type} project about: '{instance.title}'"
        
        action_url = f"/dashboard/community/collaborations/{instance.id}/"
        
        send_notification(
            instance.recipient,
            'collaboration_request',
            recipient_title,
            recipient_message,
            action_url=action_url,
            metadata={'collaboration_request_id': instance.id, 'requester_id': instance.requester.id}
        )
        
        # Notification to requester: "You sent a collaboration request to X"
        requester_title = f"Collaboration request sent to {recipient_name}"
        requester_message = f"You sent a {instance.collaboration_type} collaboration request to {recipient_name} about: '{instance.title}'. They will be notified."
        
        send_notification(
            instance.requester,
            'collaboration_request_sent',
            requester_title,
            requester_message,
            action_url=action_url,
            metadata={'collaboration_request_id': instance.id, 'recipient_id': instance.recipient.id}
        )
    except Exception as e:
        logger.warning(f"Failed to send collaboration notification: {e}")


# Additional engagement logging signals
from django.db.models.signals import post_delete
import logging
logger = logging.getLogger(__name__)

try:
    from .models import PostReaction, Comment, PostBookmark, GroupMembership, EngagementLog
except Exception:
    PostReaction = None
    Comment = None
    PostBookmark = None
    GroupMembership = None
    EngagementLog = None


@receiver(post_save)
def log_engagement_on_create(sender, instance, created, **kwargs):
    try:
        if not created:
            return
        if PostReaction is not None and sender == PostReaction:
            try:
                EngagementLog.objects.create(user=instance.user, action_type='like', post=instance.post, metadata={'reaction_type': getattr(instance, 'reaction_type', None)})
            except Exception:
                logger.exception('Failed to create engagement log for PostReaction')
            return

        if Comment is not None and sender == Comment:
            try:
                EngagementLog.objects.create(user=instance.author, action_type='comment', post=instance.post, comment=instance)
            except Exception:
                logger.exception('Failed to create engagement log for Comment')
            return

        if PostBookmark is not None and sender == PostBookmark:
            try:
                EngagementLog.objects.create(user=instance.user, action_type='bookmark', post=instance.post)
            except Exception:
                logger.exception('Failed to create engagement log for PostBookmark')
            return

        if GroupMembership is not None and sender == GroupMembership:
            try:
                EngagementLog.objects.create(user=instance.user, action_type='group_join', group=instance.group)
            except Exception:
                logger.exception('Failed to create engagement log for GroupMembership')
            return
    except Exception:
        logger.exception('Unhandled error in log_engagement_on_create')


@receiver(post_delete)
def log_engagement_on_delete(sender, instance, **kwargs):
    try:
        if PostReaction is not None and sender == PostReaction:
            try:
                EngagementLog.objects.create(user=getattr(instance, 'user', None), action_type='unlike', post=getattr(instance, 'post', None))
            except Exception:
                logger.exception('Failed to create engagement log for PostReaction deletion')
    except Exception:
        logger.exception('Unhandled error in log_engagement_on_delete')
