"""
Management command: create_default_admin
Idempotently creates the default admin account on any environment (local/production).
Safe to run multiple times - will update password if user already exists.

Usage:
    python manage.py create_default_admin
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Admin, AdminProfile


class Command(BaseCommand):
    help = "Create or update the default Bhanu_admin account (idempotent)"

    def handle(self, *args, **options):
        # Credentials (can be overridden via environment variables)
        username = os.environ.get('DEFAULT_ADMIN_USERNAME', 'Bhanu_admin')
        password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin@123')
        email    = os.environ.get('DEFAULT_ADMIN_EMAIL',    'bhanu@midpointschool.online')
        name     = os.environ.get('DEFAULT_ADMIN_NAME',     'Bhanu Kumar Singh')

        # Step 1: Create / update Django User
        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.email        = email
        user.first_name   = name.split()[0]
        user.last_name    = ' '.join(name.split()[1:])
        user.is_staff     = True
        user.is_superuser = True
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            "[OK] Django User {}: username={}, email={}".format(action, username, email)
        ))

        # Step 2: Ensure AdminProfile exists for 2FA
        profile, _ = AdminProfile.objects.get_or_create(user=user)
        self.stdout.write(self.style.SUCCESS(
            "[OK] AdminProfile ready | telegram_chat_id={}".format(
                profile.telegram_chat_id or 'Not linked yet'
            )
        ))

        # Step 3: Create / update legacy Admin model entry
        admin, admin_created = Admin.objects.get_or_create(
            email=email,
            defaults={
                'name': name,
                'phone': '',
                'role': 'Administrator',
            }
        )
        admin.name = name
        admin.set_password(password)
        admin.save()

        admin_action = "Created" if admin_created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            "[OK] Admin entry {}: email={}".format(admin_action, email)
        ))

        self.stdout.write(self.style.SUCCESS(
            "\n========================================\n"
            " Admin account ready!\n"
            "   Username : {}\n"
            "   Password : {}\n"
            "   Login at : /admin-login/\n"
            "========================================".format(username, password)
        ))
