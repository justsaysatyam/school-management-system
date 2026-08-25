"""
Management command: create_default_admin
Idempotently creates/updates the default admin accounts on any environment (local/production).
Safe to run multiple times - will update passwords and telegram_chat_ids.

Usage:
    python manage.py create_default_admin
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Admin, AdminProfile


ADMIN_ACCOUNTS = [
    {
        'username': 'admin',
        'email': 'admin@midpoint.com',
        'password': 'admin123',
        'name': 'Administrator',
        'telegram_chat_id': '5215400355',
    },
    {
        'username': 'Bhanu_admin',
        'email': 'bhanu@midpointschool.online',
        'password': 'admin@123',
        'name': 'Bhanu Kumar Singh',
        'telegram_chat_id': '1949979666',
    },
]


class Command(BaseCommand):
    help = "Create or update permanent admin accounts with Telegram 2FA chat IDs (idempotent)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding permanent admin accounts..."))

        for acc in ADMIN_ACCOUNTS:
            username = acc['username']
            email = acc['email']
            password = acc['password']
            name = acc['name']
            telegram_chat_id = acc['telegram_chat_id']

            # 1. Create or update Django User by username or email
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.filter(email=email).first()

            if not user:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                )
                action = "Created"
            else:
                user.username = username
                user.email = email
                user.set_password(password)
                action = "Updated"

            user.first_name = name.split()[0]
            user.last_name = ' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
            user.is_staff = True
            user.is_superuser = True
            user.save()

            self.stdout.write(self.style.SUCCESS(
                f"[OK] Django User {action}: username={username}, email={email}"
            ))

            # 2. Ensure AdminProfile exists and set permanent Telegram Chat ID
            profile, _ = AdminProfile.objects.get_or_create(user=user)
            profile.telegram_chat_id = telegram_chat_id
            profile.save()

            self.stdout.write(self.style.SUCCESS(
                f"[OK] AdminProfile linked: telegram_chat_id={profile.telegram_chat_id}"
            ))

            # 3. Create or update legacy Admin model entry
            admin_entry, admin_created = Admin.objects.get_or_create(
                email=email,
                defaults={
                    'name': name,
                    'phone': '',
                    'role': 'Administrator',
                }
            )
            admin_entry.name = name
            admin_entry.set_password(password)
            admin_entry.save()

            admin_action = "Created" if admin_created else "Updated"
            self.stdout.write(self.style.SUCCESS(
                f"[OK] Legacy Admin entry {admin_action}: email={email}"
            ))

        self.stdout.write(self.style.SUCCESS(
            "\n========================================\n"
            " All Admin accounts permanently ready!\n"
            " Admin 1: admin@midpoint.com (Chat ID: 5215400355)\n"
            " Admin 2: bhanu@midpointschool.online (Chat ID: 1949979666)\n"
            "========================================"
        ))
