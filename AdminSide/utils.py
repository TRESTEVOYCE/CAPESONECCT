# utils.py
from .models import Notification, User

def send_notification(recipient, title, message, notification_type, sender=None, reason=None, target_url=None):
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        title=title,
        message=message,
        reason=reason,
        notification_type=notification_type,
        target_url=target_url
    )


def notify_admins(title, message, notification_type, sender=None, reason=None, target_url=None):
    return [
        send_notification(
            recipient=admin,
            title=title,
            message=message,
            notification_type=notification_type,
            sender=sender,
            reason=reason,
            target_url=target_url,
        )
        for admin in User.objects.filter(is_superuser=True)
    ]