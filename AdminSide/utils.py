# utils.py
from django.db.models import Q
from django.urls import reverse
from .models import Notification, User


def get_admin_users():
    return User.objects.filter(
        Q(role__in=['admin', 'peso']) | (Q(is_superuser=True) & ~Q(role='employer'))
    ).distinct()


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


def notify_employer_verified(employer, sender):
    return send_notification(
        recipient=employer.user,
        sender=sender,
        title='Employer Account Verified',
        message='Your employer account has been verified. You can now access employer features.',
        notification_type='VERIFICATION_APPROVED',
        target_url=reverse('company_profile_view'),
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
        for admin in get_admin_users()
    ]