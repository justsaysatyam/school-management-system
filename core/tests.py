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


class DigitalSignatureTestCase(TestCase):
    """Test suite for Principal and Teacher digital signature features and auto-fill resolution"""

    def setUp(self):
        from core.models import SchoolClass, Teacher, Student, SchoolInfo
        from datetime import date
        self.client = Client()

        # Create SchoolInfo
        self.school_info = SchoolInfo.objects.create(
            school_name="Mid Point School",
            principal_name="Raja Ram Kumar",
            principal_signature_url="https://example.com/principal_sig.png"
        )

        # Create School Class
        self.school_class = SchoolClass.objects.create(
            class_name="10",
            section="A",
            strength=40
        )

        # Create Teacher 1 (without signature)
        self.teacher1 = Teacher.objects.create(
            name="Teacher One",
            email="teacher1@test.com",
            mobile="9876543211",
            joining_date=date(2024, 1, 1),
            monthly_salary=25000,
        )
        self.teacher1.set_password("pass123")
        self.teacher1.save()
        self.teacher1.class_section.add(self.school_class)

        # Create Teacher 2 (with signature)
        self.teacher2 = Teacher.objects.create(
            name="Teacher Two",
            email="teacher2@test.com",
            mobile="9876543212",
            joining_date=date(2024, 1, 2),
            monthly_salary=26000,
            signature_url="https://example.com/teacher2_sig.png"
        )
        self.teacher2.set_password("pass123")
        self.teacher2.save()
        self.teacher2.class_section.add(self.school_class)

        # Create Student in this class
        self.student = Student.objects.create(
            name="Rahul Sharma",
            father_name="Suresh Sharma",
            student_class=self.school_class,
            mobile="9876543210",
            admission_date=date(2024, 1, 1),
            monthly_fee=1500,
        )
        self.student.set_password("stud123")
        self.student.save()

    def test_class_teacher_multi_resolution_picks_first_with_signature(self):
        """When a class has multiple teachers, get_class_teacher_for_student should pick the teacher who uploaded signature."""
        from core.views import get_class_teacher_for_student
        resolved_teacher = get_class_teacher_for_student(self.student)
        self.assertIsNotNone(resolved_teacher)
        self.assertEqual(resolved_teacher.pk, self.teacher2.pk)
        self.assertEqual(resolved_teacher.name, "Teacher Two")

    def test_admin_school_settings_view_accessible_by_admin(self):
        """Admin can access /admin/school-settings/ page."""
        session = self.client.session
        session['user_type'] = 'admin'
        session.save()

        response = self.client.get(reverse('admin_school_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Principal Digital Signature')

    def test_teacher_profile_signature_upload(self):
        """Teacher can update their digital signature URL from profile."""
        session = self.client.session
        session['user_type'] = 'teacher'
        session['teacher_id'] = self.teacher1.id
        session.save()

        response = self.client.post(reverse('teacher_profile'), {
            'signature_url': 'https://example.com/teacher1_sig.png'
        })
        self.assertRedirects(response, reverse('teacher_profile'))
        self.teacher1.refresh_from_db()
        self.assertEqual(self.teacher1.signature_url, 'https://example.com/teacher1_sig.png')

    def test_serve_binary_redirects_for_signature_urls(self):
        """serve_binary redirects to external signature URL if set."""
        # Principal signature
        response = self.client.get(
            reverse('serve_binary', kwargs={
                'model_name': 'SchoolInfo',
                'record_id': self.school_info.id,
                'field_name': 'principal_signature'
            })
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://example.com/principal_sig.png")

        # Teacher signature
        response = self.client.get(
            reverse('serve_binary', kwargs={
                'model_name': 'Teacher',
                'record_id': self.teacher2.id,
                'field_name': 'signature'
            })
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://example.com/teacher2_sig.png")

