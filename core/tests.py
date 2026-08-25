import time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Admin, AdminProfile
from core.utils import generate_otp, send_telegram_otp


class AdminAuthTestCase(TestCase):
    """Test suite for Admin Telegram 2FA authentication flow."""

    def setUp(self):
        self.client = Client()
        self.email = "admin@test.com"
        self.password = "SecurePass123!"
        self.telegram_chat_id = "123456789"

        # Create Django User
        self.user = User.objects.create_user(
            username="admin_test",
            email=self.email,
            password=self.password,
            is_staff=True,
            is_superuser=True,
        )
        # Create legacy Admin object
        self.admin_obj = Admin.objects.create(
            name="Test Admin",
            email=self.email,
            phone="+919876543210",
            role="Administrator",
        )
        self.admin_obj.set_password(self.password)
        self.admin_obj.save()

    # ── Utilities ─────────────────────────────────────────────────────────────

    def test_otp_generation_is_6_numeric_digits(self):
        otp = generate_otp(6)
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    # ── Login flow without Telegram Chat ID ───────────────────────────────────

    def test_login_without_chat_id_redirects_to_register_telegram(self):
        """Admin without a linked Chat ID should be sent to onboarding."""
        # Ensure no chat ID on the profile
        profile, _ = AdminProfile.objects.get_or_create(user=self.user)
        profile.telegram_chat_id = None
        profile.save()

        response = self.client.post(reverse('admin_login'), {
            'email': self.email,
            'password': self.password,
        })
        self.assertRedirects(response, reverse('admin_register_telegram'), fetch_redirect_response=False)
        self.assertIn('pending_telegram_reg_user_id', self.client.session)

    # ── Login flow WITH Telegram Chat ID (2FA) ─────────────────────────────

    def test_login_with_chat_id_redirects_to_verify_otp(self):
        """Admin with a linked Chat ID should be sent to OTP verification."""
        profile, _ = AdminProfile.objects.get_or_create(user=self.user)
        profile.telegram_chat_id = self.telegram_chat_id
        profile.save()

        response = self.client.post(reverse('admin_login'), {
            'email': self.email,
            'password': self.password,
        })
        self.assertRedirects(response, reverse('admin_verify_otp'), fetch_redirect_response=False)
        self.assertIn('pre_2fa_user_id', self.client.session)
        self.assertIn('otp_code', self.client.session)
        self.assertIn('otp_expires_at', self.client.session)

    # ── OTP verification ──────────────────────────────────────────────────────

    def _set_otp_session(self, otp='654321', offset=300):
        session = self.client.session
        session['pre_2fa_user_id'] = self.user.id
        session['otp_code'] = otp
        session['otp_expires_at'] = int(time.time()) + offset
        session['otp_last_sent_at'] = int(time.time())
        session.save()

    def test_otp_correct_logs_in_and_redirects_to_dashboard(self):
        self._set_otp_session('654321')
        response = self.client.post(reverse('admin_verify_otp'), {'otp_code': '654321'})
        self.assertRedirects(response, reverse('admin_dashboard'), fetch_redirect_response=False)
        self.assertEqual(self.client.session.get('user_type'), 'admin')
        self.assertNotIn('pre_2fa_user_id', self.client.session)

    def test_otp_wrong_code_shows_error(self):
        self._set_otp_session('654321')
        response = self.client.post(reverse('admin_verify_otp'), {'otp_code': '000000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Incorrect OTP')

    def test_otp_expired_shows_error(self):
        self._set_otp_session('654321', offset=-10)  # expired 10 seconds ago
        response = self.client.post(reverse('admin_verify_otp'), {'otp_code': '654321'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'expired')

    # ── Invalid credentials ───────────────────────────────────────────────────

    def test_wrong_password_returns_error(self):
        response = self.client.post(reverse('admin_login'), {
            'email': self.email,
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid password')
