import os

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from accounts.models import StaffProfile


class Command(BaseCommand):
    help = "Create the default staff account from environment variables"

    def handle(self, *args, **options):

        username = os.getenv("DJANGO_STAFF_USERNAME", "").strip()
        password = os.getenv("DJANGO_STAFF_PASSWORD", "")
        email = os.getenv("DJANGO_STAFF_EMAIL", "").strip()

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Staff environment variables are not configured. "
                    "Skipping staff account creation."
                )
            )
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": False,
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = False
            user.is_active = True
            user.save()

            StaffProfile.objects.update_or_create(
                user=user,
                defaults={
                    "role": "staff",
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Staff account '{username}' created successfully."
                )
            )

        else:
            StaffProfile.objects.update_or_create(
                user=user,
                defaults={
                    "role": "staff",
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Staff account '{username}' already exists."
                )
            )