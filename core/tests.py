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


class AdminChangeCredentialsTestCase(TestCase):
    """Test suite for Admin change credentials flow."""

    def setUp(self):
        self.client = Client()
        self.email = "test_bhanu@midpointschool.online"
        self.username = "Test_Bhanu_Admin"
        self.password = "admin@123"
        self.telegram_chat_id = "1949979666"

        self.user, _ = User.objects.get_or_create(
            username=self.username,
            defaults={
                'email': self.email,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        self.user.set_password(self.password)
        self.user.save()

        self.profile, _ = AdminProfile.objects.get_or_create(
            user=self.user,
            defaults={'telegram_chat_id': self.telegram_chat_id}
        )
        self.profile.telegram_chat_id = self.telegram_chat_id
        self.profile.save()

        self.admin_obj, _ = Admin.objects.get_or_create(
            email=self.email,
            defaults={
                'name': "Bhanu Kumar Singh",
                'role': "Administrator",
            }
        )
        self.admin_obj.set_password(self.password)
        self.admin_obj.save()

    def test_change_credentials_case_insensitive_username(self):
        """Entering lowercase username should successfully authenticate and send OTP."""
        session = self.client.session
        session['user_type'] = 'admin'
        session.save()

        from unittest.mock import patch
        with patch('core.views.send_telegram_otp', return_value=(True, "OK")):
            response = self.client.post(reverse('admin_change_credentials'), {
                'current_username': 'test_bhanu_admin',  # Lowercase
                'current_password': self.password,
                'new_password': 'NewPassword@123',
                'confirm_password': 'NewPassword@123',
            })
            self.assertRedirects(response, reverse('admin_change_credentials_verify_otp'), fetch_redirect_response=False)
            self.assertEqual(self.client.session.get('creds_change_user_id'), self.user.id)

    def test_change_credentials_via_email(self):
        """Entering email should successfully authenticate and send OTP."""
        session = self.client.session
        session['user_type'] = 'admin'
        session.save()

        from unittest.mock import patch
        with patch('core.views.send_telegram_otp', return_value=(True, "OK")):
            response = self.client.post(reverse('admin_change_credentials'), {
                'current_username': self.email,
                'current_password': self.password,
                'new_username': 'Bhanu_new',
                'new_password': 'NewPassword@123',
                'confirm_password': 'NewPassword@123',
            })
            self.assertRedirects(response, reverse('admin_change_credentials_verify_otp'), fetch_redirect_response=False)

    def test_verify_otp_updates_user_and_admin_model(self):
        """Verifying OTP applies password and username updates across User and Admin models."""
        session = self.client.session
        session['user_type'] = 'admin'
        session['creds_change_user_id'] = self.user.id
        session['creds_change_new_username'] = 'Bhanu_new'
        session['creds_change_new_password'] = 'NewPassword@123'
        session['creds_change_otp'] = '112233'
        session['creds_change_otp_expires'] = int(time.time()) + 300
        session.save()

        response = self.client.post(reverse('admin_change_credentials_verify_otp'), {
            'otp_code': '112233',
        })
        self.assertRedirects(response, reverse('admin_login'), fetch_redirect_response=False)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'Bhanu_new')
        self.assertTrue(self.user.check_password('NewPassword@123'))

        self.admin_obj.refresh_from_db()
        self.assertTrue(self.admin_obj.check_password('NewPassword@123'))


class TelegramAlertsTestCase(TestCase):
    """Test suite for Telegram alert dispatching (Inquiries & Complaints)"""

    def setUp(self):
        from unittest.mock import patch
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username="admin_notif_test",
            email="admin_notif@test.com",
            password="Password123!",
            is_staff=True
        )
        self.profile, _ = AdminProfile.objects.get_or_create(user=self.admin_user)
        self.profile.telegram_chat_id = "987654321"
        self.profile.save()

    def test_send_telegram_message_success(self):
        """send_telegram_message returns True when Telegram API responds ok."""
        from unittest.mock import patch, MagicMock
        from core.utils import send_telegram_message

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"ok": True, "result": {"message_id": 12345}}

        with patch('requests.post', return_value=mock_resp):
            success, info = send_telegram_message("987654321", "Test Message")
            self.assertTrue(success)
            self.assertEqual(info, "12345")

    def test_send_inquiry_telegram_alert_broadcasts_to_admins(self):
        """send_inquiry_telegram_alert dispatches messages to all registered admin chat IDs."""
        from unittest.mock import patch
        from core.utils import send_inquiry_telegram_alert
        from core.models import Inquiry

        inquiry = Inquiry.objects.create(
            name="Aarav Sharma",
            email="aarav@example.com",
            mobile="9876543210",
            subject="Class 11 Admission",
            message="Looking for commerce admission details."
        )

        expected_count = AdminProfile.objects.exclude(telegram_chat_id__isnull=True).exclude(telegram_chat_id__exact='').count()
        with patch('core.utils.send_telegram_message', return_value=(True, "101")) as mock_send:
            results = send_inquiry_telegram_alert(inquiry)
            self.assertEqual(results['total'], expected_count)
            self.assertEqual(results['sent'], expected_count)
            self.assertEqual(results['failed'], 0)
            self.assertEqual(mock_send.call_count, expected_count)
            # Verify our test admin received the alert with details
            admin_call_found = any(c[0][0] == "987654321" and "Aarav Sharma" in c[0][1] and "Class 11 Admission" in c[0][1] for c in mock_send.call_args_list)
            self.assertTrue(admin_call_found)

    def test_send_complaint_telegram_alert_broadcasts_to_admins(self):
        """send_complaint_telegram_alert dispatches messages to all registered admin chat IDs."""
        from unittest.mock import patch
        from datetime import date
        from core.utils import send_complaint_telegram_alert
        from core.models import SchoolClass, Student, Complaint

        school_class = SchoolClass.objects.create(class_name="10", section="A")
        student = Student.objects.create(
            name="Rohan Verma",
            father_name="Sanjay Verma",
            student_class=school_class,
            mobile="9876500000",
            admission_date=date.today()
        )
        complaint = Complaint.objects.create(
            student=student,
            subject="Library Book Availability",
            description="Physics reference books are out of stock in the library."
        )

        expected_count = AdminProfile.objects.exclude(telegram_chat_id__isnull=True).exclude(telegram_chat_id__exact='').count()
        with patch('core.utils.send_telegram_message', return_value=(True, "102")) as mock_send:
            results = send_complaint_telegram_alert(complaint)
            self.assertEqual(results['total'], expected_count)
            self.assertEqual(results['sent'], expected_count)
            self.assertEqual(results['failed'], 0)
            self.assertEqual(mock_send.call_count, expected_count)
            # Verify our test admin received the complaint alert with details
            admin_call_found = any(c[0][0] == "987654321" and "Rohan Verma" in c[0][1] and "Library Book Availability" in c[0][1] for c in mock_send.call_args_list)
            self.assertTrue(admin_call_found)

    def test_inquiry_submission_triggers_telegram_alert(self):
        """Submitting the public inquiry form triggers send_inquiry_telegram_alert."""
        from unittest.mock import patch
        with patch('core.views.send_inquiry_telegram_alert') as mock_alert:
            response = self.client.post(reverse('home'), {
                'inquiry_submit': '1',
                'name': 'Pooja Patel',
                'email': 'pooja@example.com',
                'mobile': '9876543211',
                'subject': 'Fee Structure',
                'message': 'Please share class 9 fee details.'
            })
            self.assertRedirects(response, reverse('home'))
            mock_alert.assert_called_once()
            inquiry_obj = mock_alert.call_args[0][0]
            self.assertEqual(inquiry_obj.name, 'Pooja Patel')

    def test_student_complaint_submission_triggers_telegram_alert(self):
        """Submitting student complaint form triggers send_complaint_telegram_alert."""
        from unittest.mock import patch
        from datetime import date
        from core.models import SchoolClass, Student

        school_class = SchoolClass.objects.create(class_name="9", section="B")
        student = Student.objects.create(
            name="Amit Kumar",
            father_name="Rajesh Kumar",
            student_class=school_class,
            mobile="9876511111",
            admission_date=date.today()
        )

        session = self.client.session
        session['user_type'] = 'student'
        session['student_id'] = student.id
        session.save()

        with patch('core.views.send_complaint_telegram_alert') as mock_alert:
            response = self.client.post(reverse('student_complaints'), {
                'subject': 'Classroom Projector Issue',
                'description': 'The projector in 9-B is flickering during science class.'
            })
            self.assertRedirects(response, reverse('student_complaints'))
            mock_alert.assert_called_once()
            complaint_obj = mock_alert.call_args[0][0]
            self.assertEqual(complaint_obj.subject, 'Classroom Projector Issue')


