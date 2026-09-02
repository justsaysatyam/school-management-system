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
    help = "Create default admin accounts if they do not exist (preserves custom passwords on redeploy)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Force reset admin passwords back to default hardcoded values',
        )

    def handle(self, *args, **options):
        reset_passwords = options.get('reset_passwords', False)
        self.stdout.write(self.style.NOTICE(
            f"Checking admin accounts... (reset_passwords={reset_passwords})"
        ))

        for acc in ADMIN_ACCOUNTS:
            username = acc['username']
            email = acc['email']
            password = acc['password']
            name = acc['name']
            telegram_chat_id = acc['telegram_chat_id']

            # 1. Check if Django User exists by username or email
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.filter(email=email).first()

            if not user:
                # Create brand new user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                )
                user.first_name = name.split()[0]
                user.last_name = ' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
                user.is_staff = True
                user.is_superuser = True
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"[CREATED] Django User: username={username}, email={email}"
                ))
            else:
                # User already exists - DO NOT overwrite custom username or password!
                if reset_passwords:
                    user.username = username
                    user.email = email
                    user.set_password(password)
                    self.stdout.write(self.style.WARNING(
                        f"[FORCE RESET] User password & username reset to defaults: {username}"
                    ))
                user.is_staff = True
                user.is_superuser = True
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"[PRESERVED] User exists, credentials preserved: username={user.username}, email={user.email}"
                ))

            # 2. Ensure AdminProfile exists (preserve custom telegram_chat_id if set)
            profile, _ = AdminProfile.objects.get_or_create(user=user)
            if not profile.telegram_chat_id or reset_passwords:
                profile.telegram_chat_id = telegram_chat_id
                profile.save()
                self.stdout.write(self.style.SUCCESS(
                    f"[OK] AdminProfile chat ID set: {profile.telegram_chat_id}"
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"[PRESERVED] AdminProfile chat ID: {profile.telegram_chat_id}"
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
            if admin_created:
                admin_entry.set_password(password)
                admin_entry.save()
                self.stdout.write(self.style.SUCCESS(
                    f"[CREATED] Legacy Admin entry: email={email}"
                ))
            elif reset_passwords:
                admin_entry.set_password(password)
                admin_entry.save()
                self.stdout.write(self.style.WARNING(
                    f"[FORCE RESET] Legacy Admin password reset: email={email}"
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"[PRESERVED] Legacy Admin entry exists: email={email}"
                ))

        self.stdout.write(self.style.SUCCESS(
            "\n========================================\n"
            " All Admin accounts permanently ready!\n"
            " Admin 1: admin@midpoint.com (Chat ID: 5215400355)\n"
            " Admin 2: bhanu@midpointschool.online (Chat ID: 1949979666)\n"
            "========================================"
        ))
