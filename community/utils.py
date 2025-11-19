from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_group_invite(invite, invite_url=None):
    """Send a group invite email. This is a safe stub that will attempt to send
    an email using Django's configured email backend. If no backend is configured
    it will log and return False.

    invite: GroupInvite instance
    invite_url: optional full URL the user can click to accept the invite
    """
    try:
        subject = f"You're invited to join the group: {invite.group.name}"
        if invite.invited_user:
            recipient = invite.invited_user.email
        else:
            recipient = invite.invited_email

        if not recipient:
            logger.warning('No email to send invite to for invite id=%s', getattr(invite, 'id', None))
            return False

        body_lines = [
            f"Hello,",
            f"\nYou have been invited to join the group '{invite.group.name}'.",
            f"\n",
            f"Accept the invite using this token: {invite.token}",
        ]

        if invite_url:
            body_lines.append(f"Or click: {invite_url}")

        message = '\n'.join(body_lines)

        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
            [recipient],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.exception('Failed to send group invite email: %s', e)
        return False
