from datetime import timedelta

from django.core.management.base import (
    BaseCommand
)

from django.utils import timezone

from AdminSide.models import User


class Command(BaseCommand):

    help = (
        'Delete user accounts that have not '
        'verified their email within 24 hours.'
    )

    def handle(self, *args, **options):

        expiration_time = (
            timezone.now()
            - timedelta(hours=24)
        )

        users = User.objects.filter(
            email_verified=False,
            email_verification_sent_at__lt=expiration_time
        )

        count = users.count()

        users.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {count} unverified account(s).'
            )
        )