# utils.py
from .models import Notification

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