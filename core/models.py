from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from decimal import Decimal


class AdminProfile(models.Model):
    """Profile for Django User model to support 2FA via Telegram Bot"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    phone_number = models.CharField(
        max_length=17,
        blank=True,
        null=True,
        help_text="Phone number in E.164 format (e.g., +91XXXXXXXXXX)"
    )
    telegram_chat_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Telegram numeric Chat ID for 2FA OTP delivery (get it from @userinfobot)"
    )

    class Meta:
        verbose_name = "Admin Profile"
        verbose_name_plural = "Admin Profiles"

    def __str__(self):
        return f"AdminProfile({self.user.username}) | Telegram: {self.telegram_chat_id or 'Not Linked'}"



class SchoolClass(models.Model):
    """Class model for organizing students by grade/class"""
    class_name = models.CharField(max_length=50)
    section = models.CharField(max_length=10)
    strength = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        unique_together = ['class_name', 'section']
    
    def __str__(self):
        return f"{self.class_name} - {self.section}"


class Subject(models.Model):
    """Subject/Course model"""
    subject_name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return f"{self.subject_name} ({self.subject_code})"


class Admin(models.Model):
    """School Administrator model"""
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=50, default='Administrator')
    photo = models.BinaryField(blank=True, null=True)
    photo_mimetype = models.CharField(max_length=100, blank=True, null=True)
    photo_filename = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return self.name



class Teacher(models.Model):
    """Teacher/Staff model"""
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    aadhar_no = models.CharField(max_length=12, blank=True)
    qualification = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=50, default='Teacher')
    joining_date = models.DateField()
    subjects = models.ManyToManyField(Subject, blank=True)
    class_section = models.ManyToManyField(SchoolClass, blank=True, related_name='class_teachers')
    password = models.CharField(max_length=128)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    photo = models.BinaryField(blank=True, null=True)
    photo_mimetype = models.CharField(max_length=100, blank=True, null=True)
    photo_filename = models.CharField(max_length=255, blank=True, null=True)
    photo_url = models.URLField(max_length=500, blank=True, null=True, help_text='External photo URL (optional, used if no uploaded photo)')
    signature = models.BinaryField(blank=True, null=True)
    signature_mimetype = models.CharField(max_length=100, blank=True, null=True)
    signature_filename = models.CharField(max_length=255, blank=True, null=True)
    signature_url = models.URLField(max_length=500, blank=True, null=True, help_text='External signature URL (optional, used if no uploaded signature)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return self.name


class Student(models.Model):
    """Student model"""
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    student_class = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True)
    role = models.CharField(max_length=50, default='Student')
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    mobile = models.CharField(max_length=15)
    admission_date = models.DateField()
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    photo = models.BinaryField(blank=True, null=True)
    photo_mimetype = models.CharField(max_length=100, blank=True, null=True)
    photo_filename = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=128)
    raw_password = models.CharField(max_length=128, blank=True, null=True, help_text='Plaintext password set by admin for registration certificate')
    is_active = models.BooleanField(default=True)
    photo_url = models.URLField(max_length=500, blank=True, null=True, help_text='External photo URL (optional, used if no uploaded photo)')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def set_password(self, raw_password):
        self.raw_password = raw_password
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def __str__(self):
        return f"{self.name} - {self.student_class}"


class TeacherPayment(models.Model):
    """Teacher salary payment records"""
    PAYMENT_MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('UPI', 'UPI'),
        ('Cheque', 'Cheque'),
    ]
    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
    ]
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='payments')
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='Cash')
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    month = models.CharField(max_length=20)
    year = models.IntegerField()
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.teacher.name} - {self.month} {self.year}"


class StudentPayment(models.Model):
    """Student fee payment records"""
    PAYMENT_MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('UPI', 'UPI'),
        ('Cheque', 'Cheque'),
    ]
    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='Cash')
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    month = models.CharField(max_length=20)
    year = models.IntegerField()
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.student.name} - {self.month} {self.year}"


class TeacherAttendance(models.Model):
    """Teacher attendance records"""
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Leave', 'Leave'),
        ('Half Day', 'Half Day'),
    ]
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    
    class Meta:
        unique_together = ['teacher', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.teacher.name} - {self.date}"


class StudentAttendance(models.Model):
    """Student attendance records"""
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Leave', 'Leave'),
        ('Half Day', 'Half Day'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student.name} - {self.date}"


class Notice(models.Model):
    """School notice/announcement model"""
    CATEGORY_CHOICES = [
        ('General', 'General'),
        ('Academic', 'Academic'),
        ('Event', 'Event'),
        ('Holiday', 'Holiday'),
        ('Exam', 'Exam'),
    ]
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]
    AUDIENCE_CHOICES = [
        ('All', 'All'),
        ('Students', 'Students'),
        ('Teachers', 'Teachers'),
        ('Parents', 'Parents'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='General')
    issued_by = models.CharField(max_length=100)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    notice_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField(null=True, blank=True)
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='All')
    file = models.BinaryField(blank=True, null=True)
    file_mimetype = models.CharField(max_length=100, blank=True, null=True)
    file_filename = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-notice_date']
    
    def __str__(self):
        return self.title


class Event(models.Model):
    """School event model"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateField()
    event_time = models.TimeField(null=True, blank=True)
    image = models.BinaryField(blank=True, null=True)
    image_mimetype = models.CharField(max_length=100, blank=True, null=True)
    image_filename = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-event_date']
    
    def __str__(self):
        return f"{self.title} - {self.event_date}"


class ExamTerm(models.Model):
    """Admin defined Exam terms/types (e.g., Half Yearly, Annual)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Exam Term"
        verbose_name_plural = "Exam Terms"

    def __str__(self):
        return self.name


class Exam(models.Model):
    """Exam schedule model"""
    exam_name = models.CharField(max_length=100)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    exam_date = models.DateField()
    exam_time = models.TimeField()
    room_no = models.CharField(max_length=20, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['exam_date', 'exam_time']
    
    def __str__(self):
        return f"{self.exam_name} - {self.school_class}"


class SchoolInfo(models.Model):
    """School information and configuration"""
    school_name = models.CharField(max_length=200, default='Mid Point School')
    address = models.TextField(default='Barahiya, Near Hanuman Temple')
    contact_number = models.CharField(max_length=15, default='7762044304')
    email = models.EmailField(default='bssingtechenterprieses@gmail.com')
    principal_name = models.CharField(max_length=100, default='Raja Ram Kumar')
    director_name = models.CharField(max_length=100, default='Manoj Kumar')
    established_year = models.IntegerField(default=2000)
    total_students = models.IntegerField(default=500)
    total_teachers = models.IntegerField(default=25)
    motto = models.CharField(max_length=200, default='Excellence in Education')
    description = models.TextField(blank=True)
    logo = models.BinaryField(blank=True, null=True)
    logo_mimetype = models.CharField(max_length=100, blank=True, null=True)
    logo_filename = models.CharField(max_length=255, blank=True, null=True)
    principal_signature = models.BinaryField(blank=True, null=True)
    principal_signature_mimetype = models.CharField(max_length=100, blank=True, null=True)
    principal_signature_filename = models.CharField(max_length=255, blank=True, null=True)
    principal_signature_url = models.URLField(max_length=500, blank=True, null=True, help_text='External Principal signature URL (optional)')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "School Information"
        verbose_name_plural = "School Information"
    
    def __str__(self):
        return self.school_name


class GalleryImage(models.Model):
    """School photo gallery"""
    CATEGORY_CHOICES = [
        ('Building', 'School Building'),
        ('Students', 'Students'),
        ('Events', 'Events'),
        ('Sports', 'Sports & PT'),
        ('Annual Day', 'Annual Day'),
        ('Other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    image = models.BinaryField(blank=True, null=True)
    image_mimetype = models.CharField(max_length=100, blank=True, null=True)
    image_filename = models.CharField(max_length=255, blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True, help_text='External image URL (optional, used if no uploaded image)')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    description = models.TextField(blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['display_order', '-upload_date']
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"
    
    def __str__(self):
        return f"{self.title} - {self.category}"


class Result(models.Model):
    """Student exam results with teacher submission and admin verification"""
    VERIFICATION_STATUS_CHOICES = [
        ('Pending', 'Pending Verification'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
    ]
    
    GRADE_CHOICES = [
        ('A+', 'A+ (90-100%)'),
        ('A', 'A (80-89%)'),
        ('B+', 'B+ (70-79%)'),
        ('B', 'B (60-69%)'),
        ('C', 'C (50-59%)'),
        ('D', 'D (40-49%)'),
        ('F', 'F (Below 40%)'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    exam_name = models.CharField(max_length=100, help_text='e.g., Half Yearly, Annual, Unit Test')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, default='F', blank=True)
    
    # Submission tracking
    submitted_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='submitted_results')
    submission_date = models.DateTimeField(auto_now_add=True)
    
    # Verification tracking
    verification_status = models.CharField(max_length=10, choices=VERIFICATION_STATUS_CHOICES, default='Pending')
    verified_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_results')
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_remarks = models.TextField(blank=True)
    
    # Additional fields
    exam_date = models.DateField()
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-submission_date']
        verbose_name = "Result"
        verbose_name_plural = "Results"
    
    def save(self, *args, **kwargs):
        # Auto-calculate percentage safely with Decimal conversion
        if self.marks_obtained is not None and self.total_marks is not None:
            try:
                m_obt = Decimal(str(self.marks_obtained))
                m_tot = Decimal(str(self.total_marks))
                self.marks_obtained = m_obt
                self.total_marks = m_tot
                
                if m_tot > 0:
                    pct = (m_obt / m_tot) * Decimal('100')
                    self.percentage = Decimal(str(round(float(pct), 2)))
                    
                    # Auto-assign grade based on percentage
                    if self.percentage >= Decimal('90'):
                        self.grade = 'A+'
                    elif self.percentage >= Decimal('80'):
                        self.grade = 'A'
                    elif self.percentage >= Decimal('70'):
                        self.grade = 'B+'
                    elif self.percentage >= Decimal('60'):
                        self.grade = 'B'
                    elif self.percentage >= Decimal('50'):
                        self.grade = 'C'
                    elif self.percentage >= Decimal('40'):
                        self.grade = 'D'
                    else:
                        self.grade = 'F'
            except Exception:
                pass
        
        if self.percentage is None:
            self.percentage = Decimal('0.00')
        if not self.grade:
            self.grade = 'F'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.name} - {self.exam_name} - {self.subject}"


class Complaint(models.Model):
    """Student complaint model for reporting issues to administration"""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='complaints')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    admin_remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"
    
    def __str__(self):
        return f"{self.student.name} - {self.subject} ({self.status})"


class Inquiry(models.Model):
    """Public inquiries from visitors on the home page"""
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    mobile = models.CharField(max_length=15)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Public Inquiry"
        verbose_name_plural = "Public Inquiries"
    
    def __str__(self):
        return f"{self.name} - {self.subject}"


class AdmitCardRequest(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    exam_term = models.ForeignKey(ExamTerm, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.school_class} - {self.exam_term}"

class ExamSchedule(models.Model):
    admit_card_request = models.ForeignKey(AdmitCardRequest, on_delete=models.CASCADE, related_name='schedules')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.subject} on {self.exam_date}"


class GradeConfig(models.Model):
    """Admin-configurable grade percentage criteria (singleton)"""
    a_plus_min = models.IntegerField(default=90, help_text='Minimum % for A+ grade')
    a_min = models.IntegerField(default=80, help_text='Minimum % for A grade')
    b_plus_min = models.IntegerField(default=70, help_text='Minimum % for B+ grade')
    b_min = models.IntegerField(default=60, help_text='Minimum % for B grade')
    c_min = models.IntegerField(default=50, help_text='Minimum % for C grade')
    d_min = models.IntegerField(default=40, help_text='Minimum % for D grade')
    pass_percentage = models.IntegerField(default=40, help_text='Minimum % to PASS')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Grade Configuration"
        verbose_name_plural = "Grade Configuration"

    def __str__(self):
        return f"Grade Config (Pass: {self.pass_percentage}%)"

    @classmethod
    def get_config(cls):
        """Get or create the singleton GradeConfig instance"""
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def get_grade(self, percentage):
        """Calculate grade for a given percentage based on current config"""
        pct = float(percentage)
        if pct >= self.a_plus_min:
            return 'A+'
        elif pct >= self.a_min:
            return 'A'
        elif pct >= self.b_plus_min:
            return 'B+'
        elif pct >= self.b_min:
            return 'B'
        elif pct >= self.c_min:
            return 'C'
        elif pct >= self.d_min:
            return 'D'
        else:
            return 'F'
