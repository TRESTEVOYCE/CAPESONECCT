import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds a default superuser account for PESO Manager handover'

    def handle(self, *args, **options):
        # Retrieve credentials from environment variables or fallback defaults
        username = os.environ.get('SEED_ADMIN_USER', 'peso_admin')
        email = os.environ.get('SEED_ADMIN_EMAIL', 'peso@municipality.gov.ph')
        password = os.environ.get('SEED_ADMIN_PASSWORD', 'PesoAdmin2026!')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name='PESO',
                last_name='Manager'
            )
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully."))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists."))