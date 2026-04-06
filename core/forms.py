from django import forms
from .models import Admin, Teacher, Student, TeacherPayment, StudentPayment, Notice, Event, SchoolClass, Subject, Complaint, Inquiry


class LoginForm(forms.Form):
    """Generic login form"""
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-input',
        'placeholder': 'Enter your email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': 'Enter your password'
    }))


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
            'subjects': forms.SelectMultiple(attrs={'class': 'form-input'}),
            'class_section': forms.Select(attrs={'class': 'form-input'}),
            'monthly_salary': forms.NumberInput(attrs={'class': 'form-input'}),
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


class StudentForm(forms.ModelForm):
    """Form for creating/editing student"""
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}), required=False)
    
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-input'}))
    
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
        photo = self.cleaned_data.get('photo')
        if photo and hasattr(photo, 'read'):
            instance.photo = photo.read()
            instance.photo_mimetype = photo.content_type
            instance.photo_filename = photo.name
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
