from django import forms
import re
from .models import Admin, Teacher, Student, TeacherPayment, StudentPayment, Notice, Event, SchoolClass, Subject, Complaint, Inquiry, SchoolInfo


class LoginForm(forms.Form):
    """Generic login form supporting either Email or Username"""
    email = forms.CharField(label="Email or Username", widget=forms.TextInput(attrs={
        'class': 'form-input',
        'placeholder': 'Enter your username or email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': 'Enter your password'
    }))


class OTPVerificationForm(forms.Form):
    """Telegram 2FA: 6-digit OTP verification"""
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        label="6-Digit OTP",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'autofocus': True,
        })
    )

    def clean_otp_code(self):
        otp = self.cleaned_data.get('otp_code', '').strip()
        if not otp.isdigit() or len(otp) != 6:
            raise forms.ValidationError("OTP must be exactly 6 digits.")
        return otp


class TelegramRegistrationForm(forms.Form):
    """Onboarding form for linking Telegram Chat ID to an admin account"""
    telegram_chat_id = forms.CharField(
        max_length=20,
        label="Telegram Chat ID",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. 123456789',
            'inputmode': 'numeric',
            'autofocus': True,
        }),
        help_text="Send any message to @userinfobot on Telegram and it will reply with your numeric Chat ID."
    )

    def clean_telegram_chat_id(self):
        chat_id = self.cleaned_data.get('telegram_chat_id', '').strip()
        # Allow optional leading minus (for group chat IDs) but otherwise numeric
        if not chat_id.lstrip('-').isdigit():
            raise forms.ValidationError("Chat ID must be a numeric value (e.g. 123456789).")
        return chat_id




class AdminForm(forms.ModelForm):
    """Form for creating/editing admin"""
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}), required=False)
    
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-input'}))
    
    class Meta:
        model = Admin
        fields = ['name', 'email', 'phone', 'address', 'role']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'role': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        photo = self.cleaned_data.get('photo')
        if photo and hasattr(photo, 'read'):
            instance.photo = photo.read()
            instance.photo_mimetype = photo.content_type
            instance.photo_filename = photo.name
        if commit:
            instance.save()
        return instance


class TeacherForm(forms.ModelForm):
    """Form for creating/editing teacher"""
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}), required=False)
    
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-input'}))
    photo_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-input',
            'placeholder': 'https://example.com/photo.jpg  (optional)'
        })
    )
    signature = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-input'}))
    signature_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-input',
            'placeholder': 'https://example.com/signature.png (optional)'
        })
    )
    
    class Meta:
        model = Teacher
        fields = ['name', 'father_name', 'email', 'mobile', 'address', 'aadhar_no', 
                  'qualification', 'role', 'joining_date', 'subjects', 'class_section', 
                  'monthly_salary', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'father_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'mobile': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'aadhar_no': forms.TextInput(attrs={'class': 'form-input'}),
            'qualification': forms.TextInput(attrs={'class': 'form-input'}),
            'role': forms.TextInput(attrs={'class': 'form-input'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'subjects': forms.CheckboxSelectMultiple(),
            'class_section': forms.CheckboxSelectMultiple(),
            'monthly_salary': forms.NumberInput(attrs={'class': 'form-input'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        photo_url = self.cleaned_data.get('photo_url')
        photo = self.cleaned_data.get('photo')
        if photo_url:
            instance.photo_url = photo_url
            instance.photo = None
            instance.photo_mimetype = None
            instance.photo_filename = None
        elif photo and hasattr(photo, 'read'):
            instance.photo = photo.read()
            instance.photo_mimetype = photo.content_type
            instance.photo_filename = photo.name
            instance.photo_url = None

        signature_url = self.cleaned_data.get('signature_url')
        signature = self.cleaned_data.get('signature')
        if signature_url:
            instance.signature_url = signature_url
            instance.signature = None
            instance.signature_mimetype = None
            instance.signature_filename = None
        elif signature and hasattr(signature, 'read'):
            instance.signature = signature.read()
            instance.signature_mimetype = signature.content_type
            instance.signature_filename = signature.name
            instance.signature_url = None

        if commit:
            instance.save()
            self._save_m2m()
        return instance


class TeacherSignatureForm(forms.Form):
    """Form for teachers to upload/update their digital signature from profile"""
    signature = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': 'image/*'
        }),
        help_text="Upload your digital signature image (transparent PNG or JPG recommended)."
    )
    signature_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-input',
            'placeholder': 'https://example.com/my-signature.png (optional)'
        }),
        help_text="Or provide a direct image link to your digital signature."
    )
    remove_signature = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput()
    )


class SchoolSettingsForm(forms.ModelForm):
    """Form for admin to manage school profile, logo, and Principal signature"""
    logo = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': 'image/*'
        })
    )
    principal_signature = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': 'image/*'
        }),
        help_text="Upload Principal's digital signature (transparent PNG recommended for PDFs)."
    )
    principal_signature_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-input',
            'placeholder': 'https://example.com/principal_signature.png (optional)'
        }),
        help_text="Or direct URL to Principal's signature."
    )
    remove_signature = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = SchoolInfo
        fields = [
            'school_name', 'address', 'contact_number', 'email',
            'principal_name', 'director_name', 'motto', 'description',
            'established_year', 'total_students', 'total_teachers'
        ]
        widgets = {
            'school_name': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'contact_number': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'principal_name': forms.TextInput(attrs={'class': 'form-input'}),
            'director_name': forms.TextInput(attrs={'class': 'form-input'}),
            'motto': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'established_year': forms.NumberInput(attrs={'class': 'form-input'}),
            'total_students': forms.NumberInput(attrs={'class': 'form-input'}),
            'total_teachers': forms.NumberInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields flexible so missing fields don't block signature upload
        for name, field in self.fields.items():
            if name != 'school_name':
                field.required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Logo handling
        logo = self.cleaned_data.get('logo')
        if logo and hasattr(logo, 'read'):
            instance.logo = logo.read()
            instance.logo_mimetype = getattr(logo, 'content_type', 'image/png')
            instance.logo_filename = getattr(logo, 'name', 'school_logo.png')

        # Principal signature handling
        remove_sig = self.cleaned_data.get('remove_signature')
        if remove_sig:
            instance.principal_signature = None
            instance.principal_signature_mimetype = None
            instance.principal_signature_filename = None
            instance.principal_signature_url = None
        else:
            sig_url = self.cleaned_data.get('principal_signature_url')
            sig_file = self.cleaned_data.get('principal_signature')
            if sig_url:
                instance.principal_signature_url = sig_url
                instance.principal_signature = None
                instance.principal_signature_mimetype = None
                instance.principal_signature_filename = None
            elif sig_file and hasattr(sig_file, 'read'):
                instance.principal_signature = sig_file.read()
                instance.principal_signature_mimetype = getattr(sig_file, 'content_type', 'image/png')
                instance.principal_signature_filename = getattr(sig_file, 'name', 'principal_signature.png')
                instance.principal_signature_url = None

        if commit:
            instance.save()
        return instance


class StudentForm(forms.ModelForm):
    """Form for creating/editing student"""
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}), required=False)
    
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-input'}))
    photo_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-input',
            'placeholder': 'https://example.com/photo.jpg  (optional)'
        })
    )
    
    class Meta:
        model = Student
        fields = ['name', 'father_name', 'student_class', 'address', 'email', 
                  'mobile', 'admission_date', 'monthly_fee', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'father_name': forms.TextInput(attrs={'class': 'form-input'}),
            'student_class': forms.Select(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'mobile': forms.TextInput(attrs={'class': 'form-input'}),
            'admission_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-input'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        photo_url = self.cleaned_data.get('photo_url')
        photo = self.cleaned_data.get('photo')
        if photo_url:
            # URL provided — save URL, clear binary photo
            instance.photo_url = photo_url
            instance.photo = None
            instance.photo_mimetype = None
            instance.photo_filename = None
        elif photo and hasattr(photo, 'read'):
            # File uploaded — save binary, clear URL
            instance.photo = photo.read()
            instance.photo_mimetype = photo.content_type
            instance.photo_filename = photo.name
            instance.photo_url = None
        if commit:
            instance.save()
        return instance


class TeacherPaymentForm(forms.ModelForm):
    """Form for teacher salary payment"""
    class Meta:
        model = TeacherPayment
        fields = ['teacher', 'payment_mode', 'paid_amount', 'due_amount', 'payment_date', 
                  'status', 'month', 'year', 'remarks']
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-input'}),
            'payment_mode': forms.Select(attrs={'class': 'form-input'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-input'}),
            'due_amount': forms.NumberInput(attrs={'class': 'form-input'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'month': forms.TextInput(attrs={'class': 'form-input'}),
            'year': forms.NumberInput(attrs={'class': 'form-input'}),
            'remarks': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class StudentPaymentForm(forms.ModelForm):
    """Form for student fee payment"""
    class Meta:
        model = StudentPayment
        fields = ['student', 'payment_mode', 'paid_amount', 'due_amount', 'payment_date', 
                  'status', 'month', 'year', 'remarks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-input'}),
            'payment_mode': forms.Select(attrs={'class': 'form-input'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-input'}),
            'due_amount': forms.NumberInput(attrs={'class': 'form-input'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'month': forms.TextInput(attrs={'class': 'form-input'}),
            'year': forms.NumberInput(attrs={'class': 'form-input'}),
            'remarks': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class NoticeForm(forms.ModelForm):
    """Form for creating notices"""
    file = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-input'}))
    
    class Meta:
        model = Notice
        fields = ['title', 'description', 'category', 'issued_by', 'priority', 
                  'valid_until', 'audience']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'issued_by': forms.TextInput(attrs={'class': 'form-input'}),
            'priority': forms.Select(attrs={'class': 'form-input'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'audience': forms.Select(attrs={'class': 'form-input'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        file = self.cleaned_data.get('file')
        if file and hasattr(file, 'read'):
            instance.file = file.read()
            instance.file_mimetype = file.content_type
            instance.file_filename = file.name
        if commit:
            instance.save()
        return instance


class ClassForm(forms.ModelForm):
    """Form for creating/editing class"""
    class Meta:
        model = SchoolClass
        fields = ['class_name', 'section', 'strength']
        widgets = {
            'class_name': forms.TextInput(attrs={'class': 'form-input'}),
            'section': forms.TextInput(attrs={'class': 'form-input'}),
            'strength': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class SubjectForm(forms.ModelForm):
    """Form for creating/editing subject"""
    class Meta:
        model = Subject
        fields = ['subject_name', 'subject_code']
        widgets = {
            'subject_name': forms.TextInput(attrs={'class': 'form-input'}),
            'subject_code': forms.TextInput(attrs={'class': 'form-input'}),
        }


class ComplaintForm(forms.ModelForm):
    """Form for students to submit complaints"""
    class Meta:
        model = Complaint
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter complaint subject'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 5,
                'placeholder': 'Provide details about your complaint'
            }),
        }


class ComplaintResolveForm(forms.ModelForm):
    """Form for admin to resolve complaints"""
    class Meta:
        model = Complaint
        fields = ['status', 'admin_remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input'}),
            'admin_remarks': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Add resolution remarks here...'
            }),
        }


class InquiryForm(forms.ModelForm):
    """Form for public inquiries on the home page"""
    class Meta:
        model = Inquiry
        fields = ['name', 'email', 'mobile', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your Email Address (Optional)'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your Mobile Number'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Subject of Inquiry'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'How can we help you?'
            }),
        }
