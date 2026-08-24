from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.apps import apps
from django.db.models import Sum, Count
from django.utils import timezone
from decimal import Decimal
from .models import (
    Admin, Teacher, Student, SchoolClass, Subject,
    TeacherPayment, StudentPayment, TeacherAttendance, StudentAttendance,
    Notice, Event, Exam, ExamTerm, SchoolInfo, GalleryImage, Result, Complaint, Inquiry,
    AdmitCardRequest, ExamSchedule, GradeConfig
)
from .forms import (
    LoginForm, TeacherForm, StudentForm, TeacherPaymentForm, 
    StudentPaymentForm, NoticeForm, ClassForm, SubjectForm,
    ComplaintForm, ComplaintResolveForm, InquiryForm
)
from django.contrib.auth.hashers import make_password

# ===================== HOME & AUTH =====================

def home(request):
    """Landing page with portfolio, login options, and results"""
    # Get or create school info
    school_info = SchoolInfo.objects.first()
    if not school_info:
        school_info = SchoolInfo.objects.create()
    
    # Get gallery images
    gallery_images = GalleryImage.objects.filter(is_active=True)[:8]
    
    if request.method == 'POST' and 'inquiry_submit' in request.POST:
        form = InquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your inquiry has been submitted successfully. We will contact you soon!')
            return redirect('home')
    else:
        form = InquiryForm()
    
    # Get recent results for public view
    recent_results = Result.objects.filter(verification_status='Verified').select_related('student', 'subject', 'student__student_class')[:5]
    
    context = {
        'school_info': school_info,
        'gallery_images': gallery_images,
        'form': form,
        'recent_results': recent_results,
    }
    return render(request, 'home.html', context)


def about_us(request):
    """About Us page view with Vision, Mission, and Managing Director details"""
    school_info = SchoolInfo.objects.first()
    if not school_info:
        school_info = SchoolInfo.objects.create()
    
    context = {
        'school_info': school_info,
        'md_name': 'Bhanu Kumar Singh',
        'md_designation': 'Managing Director',
    }
    return render(request, 'about_us.html', context)


def contact_us(request):
    """Contact Us page view with public inquiry submission form"""
    school_info = SchoolInfo.objects.first()
    if not school_info:
        school_info = SchoolInfo.objects.create()
    
    if request.method == 'POST' and 'inquiry_submit' in request.POST:
        form = InquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your inquiry has been submitted successfully! We will get back to you shortly.')
            return redirect('contact_us')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = InquiryForm()
    
    context = {
        'school_info': school_info,
        'form': form,
    }
    return render(request, 'contact_us.html', context)



def admin_login(request):
    """Admin login view"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                admin = Admin.objects.get(email=email)
                if admin.check_password(password):
                    request.session['admin_id'] = admin.id
                    request.session['user_type'] = 'admin'
                    request.session['user_name'] = admin.name
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, 'Invalid password')
            except Admin.DoesNotExist:
                messages.error(request, 'Admin not found')
    else:
        form = LoginForm()
    return render(request, 'admin_portal/login.html', {'form': form})


def teacher_login(request):
    """Teacher login view"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                teacher = Teacher.objects.get(email=email, is_active=True)
                if teacher.check_password(password):
                    request.session['teacher_id'] = teacher.id
                    request.session['user_type'] = 'teacher'
                    request.session['user_name'] = teacher.name
                    return redirect('teacher_dashboard')
                else:
                    messages.error(request, 'Invalid password')
            except Teacher.DoesNotExist:
                messages.error(request, 'Teacher not found')
    else:
        form = LoginForm()
    return render(request, 'teacher/login.html', {'form': form})


def student_login(request):
    """Student login view"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Use filter instead of get to handle multiple students with same email (e.g. siblings)
            students = Student.objects.filter(email=email, is_active=True)
            
            if not students.exists():
                messages.error(request, 'Student not found')
            else:
                found_student = None
                for student in students:
                    if student.check_password(password):
                        found_student = student
                        break
                
                if found_student:
                    request.session['student_id'] = found_student.id
                    request.session['user_type'] = 'student'
                    request.session['user_name'] = found_student.name
                    return redirect('student_dashboard')
                else:
                    messages.error(request, 'Invalid password')
    else:
        form = LoginForm()
    return render(request, 'student/login.html', {'form': form})


def logout(request):
    """Logout for all user types"""
    request.session.flush()
    messages.success(request, 'Logged out successfully')
    return redirect('home')


# ===================== ADMIN DASHBOARD =====================

def admin_required(view_func):
    """Decorator to require admin login"""
    def wrapper(request, *args, **kwargs):
        if request.session.get('user_type') != 'admin':
            messages.error(request, 'Please login as admin')
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_dashboard(request):
    """Admin main dashboard with financial overview"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    # Financial calculations
    total_revenue = StudentPayment.objects.filter(status='Paid').aggregate(
        total=Sum('paid_amount'))['total'] or Decimal('0')
    total_spend = TeacherPayment.objects.filter(status='Paid').aggregate(
        total=Sum('paid_amount'))['total'] or Decimal('0')
    net_income = total_revenue - total_spend
    
    # Counts
    total_students = Student.objects.filter(is_active=True).count()
    total_teachers = Teacher.objects.filter(is_active=True).count()
    total_classes = SchoolClass.objects.count()
    
    # Recent payments
    recent_fee_payments = StudentPayment.objects.order_by('-payment_date')[:5]
    recent_salary_payments = TeacherPayment.objects.order_by('-payment_date')[:5]
    
    # Pending payments
    pending_fees = StudentPayment.objects.filter(status='Pending').count()
    pending_salaries = TeacherPayment.objects.filter(status='Pending').count()
    
    # Recent notices
    recent_notices = Notice.objects.filter(is_active=True)[:5]
    
    context = {
        'total_revenue': total_revenue,
        'total_spend': total_spend,
        'net_income': net_income,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'recent_fee_payments': recent_fee_payments,
        'recent_salary_payments': recent_salary_payments,
        'pending_fees': pending_fees,
        'pending_salaries': pending_salaries,
        'recent_notices': recent_notices,
    }
    return render(request, 'admin_portal/dashboard.html', context)


# ===================== STUDENT MANAGEMENT =====================

def student_list(request):
    """List all students"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    students = Student.objects.all().select_related('student_class')
    classes = SchoolClass.objects.all()
    
    # Filter by class if provided
    class_filter = request.GET.get('class')
    selected_class_id = None
    if class_filter:
        try:
            selected_class_id = int(class_filter)
            students = students.filter(student_class_id=selected_class_id)
        except ValueError:
            pass
    
    context = {
        'students': students,
        'classes': classes,
        'selected_class_id': selected_class_id
    }
    return render(request, 'admin_portal/student_list.html', context)


def student_add(request):
    """Add new student"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            password = request.POST.get('password')
            if password:
                student.set_password(password)
            student.save()
            messages.success(request, f'Student {student.name} added successfully')
            return redirect('student_list')
    else:
        form = StudentForm()
    
    return render(request, 'admin_portal/student_form.html', {'form': form, 'title': 'Add Student'})


def student_edit(request, pk):
    """Edit student"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save(commit=False)
            password = request.POST.get('password')
            if password:
                student.set_password(password)
            student.save()
            messages.success(request, f'Student {student.name} updated successfully')
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'admin_portal/student_form.html', {'form': form, 'title': 'Edit Student', 'student': student})


def student_delete(request, pk):
    """Delete student"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    student = get_object_or_404(Student, pk=pk)
    student.delete()
    messages.success(request, 'Student deleted successfully')
    return redirect('student_list')


def student_id_card(request, pk):
    """Admin view to generate student ID card"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'admin_portal/student_id_card.html', {'student': student})


def teacher_id_card(request, pk):
    """Admin view to generate teacher ID card"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    teacher = get_object_or_404(Teacher, pk=pk)
    school_info = SchoolInfo.objects.first()
    return render(request, 'admin_portal/teacher_id_card.html', {
        'teacher': teacher,
        'school_info': school_info
    })


# ===================== TEACHER MANAGEMENT =====================

def teacher_list(request):
    """List all teachers"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    teachers = Teacher.objects.all().prefetch_related('class_section', 'subjects')
    return render(request, 'admin_portal/teacher_list.html', {'teachers': teachers})


def teacher_add(request):
    """Add new teacher"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            password = request.POST.get('password')
            if not password:
                messages.error(request, 'Password is required for new teacher')
                return render(request, 'admin_portal/teacher_form.html', {'form': form, 'title': 'Add Teacher'})
            
            teacher = form.save(commit=False)
            teacher.set_password(password)
            teacher.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, f'Teacher {teacher.name} added successfully')
            return redirect('teacher_list')
        else:
            messages.error(request, 'Please correct the errors below')
    else:
        form = TeacherForm()
    
    return render(request, 'admin_portal/teacher_form.html', {'form': form, 'title': 'Add Teacher'})


def teacher_edit(request, pk):
    """Edit teacher"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            teacher = form.save(commit=False)
            password = request.POST.get('password')
            if password:
                teacher.set_password(password)
            teacher.save()
            form.save_m2m()
            messages.success(request, f'Teacher {teacher.name} updated successfully')
            return redirect('teacher_list')
    else:
        form = TeacherForm(instance=teacher)
    
    return render(request, 'admin_portal/teacher_form.html', {'form': form, 'title': 'Edit Teacher', 'teacher': teacher})


def teacher_delete(request, pk):
    """Delete teacher"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    teacher = get_object_or_404(Teacher, pk=pk)
    teacher.delete()
    messages.success(request, 'Teacher deleted successfully')
    return redirect('teacher_list')


# ===================== FEE MANAGEMENT =====================

def fee_collection(request):
    """View all fee payments with class and status filters"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    payments = StudentPayment.objects.all().select_related('student', 'student__student_class')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        payments = payments.filter(status=status)
    
    # Filter by class
    class_id = request.GET.get('class_id')
    if class_id:
        payments = payments.filter(student__student_class__id=class_id)
    
    all_classes = SchoolClass.objects.all().order_by('class_name', 'section')
    
    context = {
        'payments': payments,
        'selected_status': status,
        'selected_class_id': class_id,
        'all_classes': all_classes,
    }
    return render(request, 'admin_portal/fee_collection.html', context)


def admin_get_students_by_class(request):
    """AJAX endpoint: return students of a given class for admin portal"""
    if request.session.get('user_type') != 'admin':
        from django.http import JsonResponse
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from django.http import JsonResponse
    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'students': []})
    students = Student.objects.filter(student_class__id=class_id, is_active=True).order_by('name')
    student_list = [{'id': s.id, 'name': s.name} for s in students]
    return JsonResponse({'students': student_list})


def fee_add(request):
    """Add new fee payment"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        form = StudentPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            messages.success(request, 'Fee payment recorded successfully')
            return redirect('fee_collection')
    else:
        form = StudentPaymentForm()
    
    all_classes = SchoolClass.objects.all().order_by('class_name', 'section')
    return render(request, 'admin_portal/fee_form.html', {
        'form': form,
        'title': 'Record Fee Payment',
        'all_classes': all_classes,
    })


def fee_edit(request, pk):
    """Edit fee payment"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    payment = get_object_or_404(StudentPayment, pk=pk)
    
    if request.method == 'POST':
        form = StudentPaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee payment updated successfully')
            return redirect('fee_collection')
    else:
        form = StudentPaymentForm(instance=payment)
    
    all_classes = SchoolClass.objects.all().order_by('class_name', 'section')
    return render(request, 'admin_portal/fee_form.html', {
        'form': form,
        'title': 'Edit Fee Payment',
        'all_classes': all_classes,
        'edit_student': payment.student,
    })



# ===================== SALARY MANAGEMENT =====================

def salary_management(request):
    """View all salary payments"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    payments = TeacherPayment.objects.all().select_related('teacher')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        payments = payments.filter(status=status)
    
    context = {
        'payments': payments,
        'selected_status': status
    }
    return render(request, 'admin_portal/salary_management.html', context)


def salary_add(request):
    """Add new salary payment"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        form = TeacherPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            messages.success(request, 'Salary payment recorded successfully')
            return redirect('salary_management')
    else:
        form = TeacherPaymentForm()
    
    return render(request, 'admin_portal/salary_form.html', {'form': form, 'title': 'Record Salary Payment'})


def salary_edit(request, pk):
    """Edit salary payment"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    payment = get_object_or_404(TeacherPayment, pk=pk)
    
    if request.method == 'POST':
        form = TeacherPaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Salary payment updated successfully')
            return redirect('salary_management')
    else:
        form = TeacherPaymentForm(instance=payment)
    
    return render(request, 'admin_portal/salary_form.html', {'form': form, 'title': 'Edit Salary Payment'})


# ===================== TEACHER ATTENDANCE MANAGEMENT =====================

def teacher_attendance_list(request):
    """View and manage teacher attendance"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    from datetime import date
    
    # Get selected date (default to today)
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = date.fromisoformat(selected_date)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # Get all active teachers
    teachers = Teacher.objects.filter(is_active=True).order_by('name')
    
    # Get attendance records for the selected date
    attendance_records = TeacherAttendance.objects.filter(date=selected_date)
    attendance_dict = {record.teacher_id: record for record in attendance_records}
    
    # Build teacher list with attendance status
    teachers_with_attendance = []
    for teacher in teachers:
        attendance = attendance_dict.get(teacher.id)
        teachers_with_attendance.append({
            'teacher': teacher,
            'attendance': attendance,
            'status': attendance.status if attendance else None
        })
    
    # Calculate summary
    present_count = attendance_records.filter(status='Present').count()
    absent_count = attendance_records.filter(status='Absent').count()
    leave_count = attendance_records.filter(status='Leave').count()
    halfday_count = attendance_records.filter(status='Half Day').count()
    
    context = {
        'teachers_with_attendance': teachers_with_attendance,
        'selected_date': selected_date,
        'present_count': present_count,
        'absent_count': absent_count,
        'leave_count': leave_count,
        'halfday_count': halfday_count,
        'total_teachers': teachers.count(),
    }
    return render(request, 'admin_portal/teacher_attendance.html', context)


def teacher_attendance_mark(request):
    """Mark or update teacher attendance"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        from datetime import date
        
        attendance_date = request.POST.get('attendance_date')
        try:
            attendance_date = date.fromisoformat(attendance_date)
        except (ValueError, TypeError):
            attendance_date = date.today()
        
        # Process attendance for each teacher
        teachers = Teacher.objects.filter(is_active=True)
        for teacher in teachers:
            status = request.POST.get(f'status_{teacher.id}')
            if status and status in ['Present', 'Absent', 'Leave', 'Half Day']:
                # Update or create attendance record
                TeacherAttendance.objects.update_or_create(
                    teacher=teacher,
                    date=attendance_date,
                    defaults={'status': status}
                )
        
        messages.success(request, f'Attendance marked successfully for {attendance_date}')
        return redirect(f'/admin/teacher-attendance/?date={attendance_date}')
    
    return redirect('teacher_attendance_list')


# ===================== NOTICE MANAGEMENT =====================

def notice_list(request):
    """List all notices - admin view"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    notices = Notice.objects.all()
    return render(request, 'admin_portal/notice_list.html', {'notices': notices})


def notice_add(request):
    """Add new notice"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notice created successfully')
            return redirect('notice_list')
    else:
        form = NoticeForm()
    
    return render(request, 'admin_portal/notice_form.html', {'form': form, 'title': 'Create Notice'})


def notice_delete(request, pk):
    """Delete notice"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    notice = get_object_or_404(Notice, pk=pk)
    notice.delete()
    messages.success(request, 'Notice deleted successfully')
    return redirect('notice_list')


# ===================== CLASS MANAGEMENT =====================

def class_list(request):
    """List all classes"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    classes = SchoolClass.objects.all()
    return render(request, 'admin_portal/class_list.html', {'classes': classes})


def class_add(request):
    """Add new class"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class created successfully')
            return redirect('class_list')
    else:
        form = ClassForm()
    
    return render(request, 'admin_portal/class_form.html', {'form': form, 'title': 'Add Class'})


def class_delete(request, pk):
    """Delete class"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    school_class = get_object_or_404(SchoolClass, pk=pk)
    school_class.delete()
    messages.success(request, 'Class deleted successfully')
    return redirect('class_list')


# ===================== SUBJECT MANAGEMENT =====================

def subject_list(request):
    """List all subjects"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    subjects = Subject.objects.all()
    return render(request, 'admin_portal/subject_list.html', {'subjects': subjects})


def subject_add(request):
    """Add new subject"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added successfully')
            return redirect('subject_list')
    else:
        form = SubjectForm()
    
    return render(request, 'admin_portal/subject_form.html', {'form': form, 'title': 'Add Subject'})


def subject_delete(request, pk):
    """Delete subject"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    subject = get_object_or_404(Subject, pk=pk)
    subject.delete()
    messages.success(request, 'Subject deleted successfully')
    return redirect('subject_list')


# ===================== EXAM TERM MANAGEMENT =====================

def exam_term_list(request):
    """Admin view for listing exam terms"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    exam_terms = ExamTerm.objects.all()
    return render(request, 'admin_portal/exam_term_list.html', {'exam_terms': exam_terms})

def exam_term_add(request):
    """Admin view for adding exam term"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            ExamTerm.objects.create(name=name, description=description, is_active=is_active)
            messages.success(request, 'Exam Term added successfully')
            return redirect('exam_term_list')
        except Exception as e:
            messages.error(request, f'Error adding Exam Term: {str(e)}')
            
    return render(request, 'admin_portal/exam_term_form.html')

def exam_term_edit(request, pk):
    """Admin view for editing exam term"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
        
    exam_term = get_object_or_404(ExamTerm, pk=pk)
    
    if request.method == 'POST':
        exam_term.name = request.POST.get('name')
        exam_term.description = request.POST.get('description', '')
        exam_term.is_active = request.POST.get('is_active') == 'on'
        
        try:
            exam_term.save()
            messages.success(request, 'Exam Term updated successfully')
            return redirect('exam_term_list')
        except Exception as e:
            messages.error(request, f'Error updating Exam Term: {str(e)}')
            
    return render(request, 'admin_portal/exam_term_form.html', {'exam_term': exam_term})

def exam_term_delete(request, pk):
    """Admin view for deleting exam term"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
        
    exam_term = get_object_or_404(ExamTerm, pk=pk)
    exam_term.delete()
    messages.success(request, 'Exam Term deleted successfully')
    return redirect('exam_term_list')

# ===================== STUDENT PORTAL =====================

def student_dashboard(request):
    """Student main dashboard"""
    if request.session.get('user_type') != 'student':
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    student = get_object_or_404(Student, pk=student_id)
    
    # Get payment summary
    payments = StudentPayment.objects.filter(student=student)
    total_paid = payments.filter(status='Paid').aggregate(total=Sum('paid_amount'))['total'] or Decimal('0')
    total_due = payments.filter(status='Pending').aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
    
    # Recent payments
    recent_payments = payments[:5]
    
    # Active notices for students
    notices = Notice.objects.filter(is_active=True, audience__in=['All', 'Students'])[:5]
    
    # Get student's verified results
    results = Result.objects.filter(student=student, verification_status='Verified').select_related('subject').order_by('-exam_date')
    
    context = {
        'student': student,
        'total_paid': total_paid,
        'total_due': total_due,
        'recent_payments': recent_payments,
        'results': results,
        'notices': notices,
        'school_info': {
            'name': 'Mid Point School',
            'address': 'Barahiya, Near Hanuman Temple',
            'contact': '6202822415',
            'email': 'bssingtechenterprieses@gmail.com'
        }
    }
    return render(request, 'student/dashboard.html', context)


def student_payment_history(request):
    """Student payment history"""
    if request.session.get('user_type') != 'student':
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    payments = StudentPayment.objects.filter(student_id=student_id)
    
    return render(request, 'student/payment_history.html', {'payments': payments})


def student_profile(request):
    """Student profile view"""
    if request.session.get('user_type') != 'student':
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    student = get_object_or_404(Student, pk=student_id)
    
    context = {
        'student': student,
        'school_info': {
            'name': 'Mid Point School',
            'address': 'Barahiya, Near Hanuman Temple',
            'contact': '6202822415',
            'email': 'bssingtechenterprieses@gmail.com'
        }
    }
    return render(request, 'student/profile.html', context)


# ===================== TEACHER PORTAL =====================

def teacher_dashboard(request):
    """Teacher main dashboard"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    # Get payment summary
    payments = TeacherPayment.objects.filter(teacher=teacher)
    total_received = payments.filter(status='Paid').aggregate(total=Sum('paid_amount'))['total'] or Decimal('0')
    pending_salary = payments.filter(status='Pending').aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
    
    # Recent payments
    recent_payments = payments[:5]
    
    # Students in teacher's class
    students = []
    if teacher.class_section.exists():
        students = Student.objects.filter(student_class__in=teacher.class_section.all(), is_active=True)
    
    # Active notices for teachers
    notices = Notice.objects.filter(is_active=True, audience__in=['All', 'Teachers'])[:5]
    
    context = {
        'teacher': teacher,
        'total_received': total_received,
        'pending_salary': pending_salary,
        'recent_payments': recent_payments,
        'students': students,
        'notices': notices,
    }
    return render(request, 'teacher/dashboard.html', context)


def teacher_salary_history(request):
    """Teacher salary history"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    teacher_id = request.session.get('teacher_id')
    payments = TeacherPayment.objects.filter(teacher_id=teacher_id)
    
    return render(request, 'teacher/salary_history.html', {'payments': payments})


def teacher_students(request):
    """Teacher view of students with class filter"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    teacher_classes = teacher.class_section.all()
    selected_class_id = request.GET.get('class_id')
    selected_class = None
    students = []
    
    if teacher_classes.exists():
        if selected_class_id:
            try:
                selected_class = teacher_classes.get(pk=selected_class_id)
                students = Student.objects.filter(student_class=selected_class, is_active=True).order_by('name')
            except SchoolClass.DoesNotExist:
                selected_class = None
        else:
            # Default: show first class
            selected_class = teacher_classes.first()
            students = Student.objects.filter(student_class=selected_class, is_active=True).order_by('name')
    
    return render(request, 'teacher/students.html', {
        'students': students,
        'teacher': teacher,
        'teacher_classes': teacher_classes,
        'selected_class': selected_class,
    })


def teacher_profile(request):
    """Teacher profile view"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    return render(request, 'teacher/profile.html', {'teacher': teacher})


# ===================== STUDENT ATTENDANCE (Teacher Portal) =====================

def student_attendance_list(request):
    """Teacher view to mark student attendance with class filter"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    from datetime import date
    
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    teacher_classes = teacher.class_section.all()
    
    # Check if teacher has a class assigned
    if not teacher_classes.exists():
        messages.warning(request, 'You are not assigned to any class')
        return render(request, 'teacher/student_attendance.html', {
            'teacher': teacher,
            'students_with_attendance': [],
            'selected_date': date.today(),
            'teacher_classes': teacher_classes,
        })
    
    # Get selected date (default to today)
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = date.fromisoformat(selected_date)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # Get selected class
    selected_class_id = request.GET.get('class_id')
    selected_class = None
    if selected_class_id:
        try:
            selected_class = teacher_classes.get(pk=selected_class_id)
        except SchoolClass.DoesNotExist:
            selected_class = None
    if not selected_class:
        selected_class = teacher_classes.first()
    
    # Get all students in selected class
    students = Student.objects.filter(
        student_class=selected_class,
        is_active=True
    ).order_by('name')
    
    # Get attendance records for the selected date
    attendance_records = StudentAttendance.objects.filter(
        date=selected_date,
        student__student_class=selected_class
    )
    attendance_dict = {record.student_id: record for record in attendance_records}
    
    # Build student list with attendance status
    students_with_attendance = []
    for student in students:
        attendance = attendance_dict.get(student.id)
        students_with_attendance.append({
            'student': student,
            'attendance': attendance,
            'status': attendance.status if attendance else None
        })
    
    # Calculate summary
    present_count = attendance_records.filter(status='Present').count()
    absent_count = attendance_records.filter(status='Absent').count()
    leave_count = attendance_records.filter(status='Leave').count()
    halfday_count = attendance_records.filter(status='Half Day').count()
    
    context = {
        'teacher': teacher,
        'teacher_classes': teacher_classes,
        'selected_class': selected_class,
        'students_with_attendance': students_with_attendance,
        'selected_date': selected_date,
        'present_count': present_count,
        'absent_count': absent_count,
        'leave_count': leave_count,
        'halfday_count': halfday_count,
        'total_students': students.count(),
    }
    return render(request, 'teacher/student_attendance.html', context)


def student_attendance_mark(request):
    """Mark student attendance by teacher"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    if request.method == 'POST':
        from datetime import date
        
        teacher_id = request.session.get('teacher_id')
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        
        if not teacher.class_section.exists():
            messages.error(request, 'You are not assigned to any class')
            return redirect('student_attendance_list')
        
        attendance_date = request.POST.get('attendance_date')
        try:
            attendance_date = date.fromisoformat(attendance_date)
        except (ValueError, TypeError):
            attendance_date = date.today()
        
        # Get the class_id from POST to process only that class
        selected_class_id = request.POST.get('class_id')
        teacher_classes = teacher.class_section.all()
        
        if selected_class_id:
            try:
                selected_class = teacher_classes.get(pk=selected_class_id)
                students = Student.objects.filter(student_class=selected_class, is_active=True)
            except SchoolClass.DoesNotExist:
                students = Student.objects.filter(student_class__in=teacher_classes, is_active=True)
        else:
            students = Student.objects.filter(student_class__in=teacher_classes, is_active=True)
        
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            if status and status in ['Present', 'Absent', 'Leave', 'Half Day']:
                # Update or create attendance record
                StudentAttendance.objects.update_or_create(
                    student=student,
                    date=attendance_date,
                    defaults={'status': status}
                )
        
        messages.success(request, f'Student attendance marked successfully for {attendance_date}')
        redirect_url = f'/teacher/student-attendance/?date={attendance_date}'
        if selected_class_id:
            redirect_url += f'&class_id={selected_class_id}'
        return redirect(redirect_url)
    
    return redirect('student_attendance_list')


# ===================== RESULTS MANAGEMENT =====================

def result_list(request):
    """Public view for searching and displaying student results"""
    school_info = SchoolInfo.objects.first()
    
    # Get filters
    student_id_raw = request.GET.get('student_id')
    class_id = request.GET.get('class_id')
    exam_name = request.GET.get('exam_name')
    
    if student_id_raw and class_id and exam_name:
        # Extract numeric ID if it starts with MPS-
        student_id_str = student_id_raw.strip().upper()
        if student_id_str.startswith('MPS-'):
            student_id_str = student_id_str[4:]
            
        try:
            student_pk = int(student_id_str)
            student = Student.objects.get(pk=student_pk, student_class_id=class_id, is_active=True)
            
            # Fetch verified results
            results = Result.objects.filter(
                student=student,
                exam_name=exam_name,
                verification_status='Verified'
            ).select_related('subject').order_by('subject__subject_name')
            
            if not results.exists():
                return render(request, 'result_list.html', {
                    'classes': SchoolClass.objects.all(),
                    'exam_names': ExamTerm.objects.filter(is_active=True).values_list('name', flat=True),
                    'error': f'No verified results found for this exam.',
                    'school_info': school_info
                })
                
            # Calculate overall totals
            total_marks_obtained = sum(r.marks_obtained for r in results)
            total_marks_total = sum(r.total_marks for r in results)
            overall_percentage = (total_marks_obtained / total_marks_total * 100) if total_marks_total > 0 else 0
            
            # Use GradeConfig for grade calculation
            grade_config = GradeConfig.get_config()
            overall_grade = grade_config.get_grade(overall_percentage)
            result_status = 'PASS' if overall_percentage >= grade_config.pass_percentage else 'FAIL'
            
            context = {
                'student': student,
                'exam_name': exam_name,
                'results': results,
                'total_subjects': results.count(),
                'total_marks_obtained': total_marks_obtained,
                'total_marks_total': total_marks_total,
                'overall_percentage': overall_percentage,
                'overall_grade': overall_grade,
                'result_status': result_status,
                'school_info': school_info,
            }
            return render(request, 'public_result_card.html', context)
            
        except (ValueError, Student.DoesNotExist):
            return render(request, 'result_list.html', {
                'classes': SchoolClass.objects.all(),
                'exam_names': ExamTerm.objects.filter(is_active=True).values_list('name', flat=True),
                'error': 'Invalid Student ID/Roll No or Class combination.',
                'school_info': school_info
            })
    
    # Just render the search form
    classes = SchoolClass.objects.all()
    exam_names = ExamTerm.objects.filter(is_active=True).values_list('name', flat=True)
    
    context = {
        'classes': classes,
        'exam_names': exam_names,
        'school_info': school_info,
    }
    return render(request, 'result_list.html', context)


def teacher_get_students_by_class(request):
    """AJAX endpoint to get students by class for teacher portal"""
    import json
    if request.session.get('user_type') != 'teacher':
        from django.http import JsonResponse
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    from django.http import JsonResponse
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    class_id = request.GET.get('class_id')
    
    if not class_id:
        return JsonResponse({'students': []})
    
    try:
        school_class = teacher.class_section.get(pk=class_id)
        students = Student.objects.filter(student_class=school_class, is_active=True).order_by('name')
        student_list = [{'id': s.id, 'name': s.name, 'class': str(s.student_class)} for s in students]
        return JsonResponse({'students': student_list})
    except SchoolClass.DoesNotExist:
        return JsonResponse({'students': [], 'error': 'Class not assigned to you'})


def result_submit(request):
    """Teacher view to submit student results with class-based student filter"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    teacher_classes = teacher.class_section.all()
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        exam_name = request.POST.get('exam_name')
        exam_date = request.POST.get('exam_date')
        remarks = request.POST.get('remarks', '')
        selected_class_id = request.POST.get('selected_class_id', '')
        
        # Arrays for multiple subjects
        subject_ids = request.POST.getlist('subject[]')
        marks_obtained_list = request.POST.getlist('marks_obtained[]')
        total_marks_list = request.POST.getlist('total_marks[]')
        
        try:
            student = Student.objects.get(pk=student_id)
            
            created_count = 0
            for i in range(len(subject_ids)):
                subject_id = subject_ids[i]
                marks_obtained = marks_obtained_list[i] if i < len(marks_obtained_list) else None
                total_marks = total_marks_list[i] if i < len(total_marks_list) else None
                
                if subject_id and marks_obtained and total_marks:
                    subject = Subject.objects.get(pk=subject_id)
                    Result.objects.create(
                        student=student,
                        exam_name=exam_name,
                        subject=subject,
                        marks_obtained=Decimal(marks_obtained),
                        total_marks=Decimal(total_marks),
                        exam_date=exam_date,
                        remarks=remarks,
                        submitted_by=teacher,
                        verification_status='Pending'
                    )
                    created_count += 1
            
            if created_count > 0:
                messages.success(request, f'Successfully submitted {created_count} results for {student.name}. Pending admin verification.')
            else:
                messages.warning(request, 'No valid results were submitted. Please check the subjects and marks.')
            return redirect('result_submit')
        except Exception as e:
            messages.error(request, f'Error submitting result: {str(e)}')
    
    subjects = Subject.objects.all()
    exam_terms = ExamTerm.objects.filter(is_active=True)
    
    # Get teacher's submitted results
    submitted_results = Result.objects.filter(submitted_by=teacher).select_related(
        'student', 'subject'
    ).order_by('-submission_date')[:20]
    
    context = {
        'teacher': teacher,
        'teacher_classes': teacher_classes,
        'subjects': subjects,
        'exam_terms': exam_terms,
        'submitted_results': submitted_results,
    }
    return render(request, 'teacher/result_submit.html', context)


def result_edit(request, pk):
    """Teacher view to edit pending results"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    teacher_id = request.session.get('teacher_id')
    result = get_object_or_404(Result, pk=pk, submitted_by_id=teacher_id)
    
    if result.verification_status != 'Pending':
        messages.error(request, 'Cannot edit verified or rejected results')
        return redirect('result_submit')
    
    if request.method == 'POST':
        result.exam_name = request.POST.get('exam_name')
        result.marks_obtained = Decimal(request.POST.get('marks_obtained'))
        result.total_marks = Decimal(request.POST.get('total_marks'))
        result.exam_date = request.POST.get('exam_date')
        result.remarks = request.POST.get('remarks', '')
        result.save()
        
        messages.success(request, 'Result updated successfully')
        return redirect('result_submit')
    
    return redirect('result_submit')


# ===================== RESULT VERIFICATION & BULK MANAGEMENT =====================

def result_verify(request):
    """Admin view to verify submitted results grouped by student with filtering and bulk actions"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    class_id = request.GET.get('class_id', '')
    exam_term = request.GET.get('exam_term', '')
    status_filter = request.GET.get('status', 'Pending')
    
    # Base queryset
    results = Result.objects.select_related(
        'student', 'student__student_class', 'subject', 'submitted_by', 'verified_by'
    ).order_by('-submission_date')
    
    if class_id:
        results = results.filter(student__student_class_id=class_id)
    if exam_term:
        results = results.filter(exam_name=exam_term)
    if status_filter and status_filter != 'All':
        results = results.filter(verification_status=status_filter)
        
    # Group results by (student, exam_name)
    grouped_students = {}
    for res in results:
        key = (res.student_id, res.exam_name)
        if key not in grouped_students:
            grouped_students[key] = {
                'student': res.student,
                'exam_name': res.exam_name,
                'results': [],
                'total_obtained': 0,
                'total_max': 0,
                'pending_count': 0,
                'verified_count': 0,
                'rejected_count': 0,
            }
        group = grouped_students[key]
        group['results'].append(res)
        group['total_obtained'] += float(res.marks_obtained or 0)
        group['total_max'] += float(res.total_marks or 0)
        if res.verification_status == 'Pending':
            group['pending_count'] += 1
        elif res.verification_status == 'Verified':
            group['verified_count'] += 1
        elif res.verification_status == 'Rejected':
            group['rejected_count'] += 1

    # Calculate percentage, grade, and overall status for each student group
    grouped_list = []
    for key, group in grouped_students.items():
        total_subj = len(group['results'])
        pct = (group['total_obtained'] / group['total_max'] * 100) if group['total_max'] > 0 else 0
        
        if pct >= 90: grade = 'A+'
        elif pct >= 80: grade = 'A'
        elif pct >= 70: grade = 'B+'
        elif pct >= 60: grade = 'B'
        elif pct >= 50: grade = 'C'
        elif pct >= 40: grade = 'D'
        else: grade = 'F'
        
        if group['pending_count'] > 0:
            status_label = 'Pending'
        elif group['rejected_count'] > 0 and group['verified_count'] == 0:
            status_label = 'Rejected'
        elif group['verified_count'] > 0 and group['pending_count'] == 0 and group['rejected_count'] == 0:
            status_label = 'Verified'
        else:
            status_label = 'Partial'
            
        group['subject_count'] = total_subj
        group['percentage'] = pct
        group['grade'] = grade
        group['status_label'] = status_label
        grouped_list.append(group)

    classes = SchoolClass.objects.all().order_by('class_name', 'section')
    exam_terms = ExamTerm.objects.filter(is_active=True).order_by('name')

    context = {
        'grouped_students': grouped_list,
        'classes': classes,
        'exam_terms': exam_terms,
        'selected_class': class_id,
        'selected_exam_term': exam_term,
        'selected_status': status_filter,
        'total_results_count': results.count(),
        'total_students_count': len(grouped_list),
    }
    return render(request, 'admin_portal/result_verify.html', context)


def result_verify_student_all(request):
    """Admin verify or reject all subject results for a specific student and exam term"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        exam_name = request.POST.get('exam_name')
        action = request.POST.get('action', 'approve') # approve or reject
        remarks = request.POST.get('remarks', '')
        
        admin_id = request.session.get('admin_id')
        admin = get_object_or_404(Admin, pk=admin_id)
        student = get_object_or_404(Student, pk=student_id)

        target_status = 'Verified' if action == 'approve' else 'Rejected'
        updated_count = Result.objects.filter(
            student=student,
            exam_name=exam_name
        ).update(
            verification_status=target_status,
            verified_by=admin,
            verification_date=timezone.now(),
            verification_remarks=remarks
        )

        if action == 'approve':
            messages.success(request, f'Verified all {updated_count} subject results for {student.name} ({exam_name})')
        else:
            messages.warning(request, f'Rejected all {updated_count} subject results for {student.name} ({exam_name})')

    # Preserve current GET params on redirect
    redirect_url = request.META.get('HTTP_REFERER') or reverse('result_verify')
    return redirect(redirect_url)


def result_verify_bulk(request):
    """Admin bulk verify or reject all results matching class / exam term filter"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        exam_name = request.POST.get('exam_name')
        status_filter = request.POST.get('status_filter', 'Pending')
        action = request.POST.get('action', 'approve')
        
        admin_id = request.session.get('admin_id')
        admin = get_object_or_404(Admin, pk=admin_id)
        
        queryset = Result.objects.all()
        if class_id:
            queryset = queryset.filter(student__student_class_id=class_id)
        if exam_name:
            queryset = queryset.filter(exam_name=exam_name)
        if status_filter and status_filter != 'All':
            queryset = queryset.filter(verification_status=status_filter)

        target_status = 'Verified' if action == 'approve' else 'Rejected'
        updated_count = queryset.update(
            verification_status=target_status,
            verified_by=admin,
            verification_date=timezone.now()
        )

        class_name = SchoolClass.objects.filter(pk=class_id).first()
        class_str = f"Class {class_name}" if class_name else "All Classes"
        exam_str = f" ({exam_name})" if exam_name else ""
        
        messages.success(request, f'Bulk Operation Complete: {updated_count} results updated to "{target_status}" for {class_str}{exam_str}')

    redirect_url = request.META.get('HTTP_REFERER') or reverse('result_verify')
    return redirect(redirect_url)


def admin_student_results_manage(request, student_id):
    """Admin view to view, edit marks, add, delete, or re-verify all subject results of a student"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')

    student = get_object_or_404(Student, pk=student_id)
    exam_filter = request.GET.get('exam', '')
    
    results = Result.objects.filter(student=student).select_related('subject', 'submitted_by', 'verified_by')
    if exam_filter:
        results = results.filter(exam_name=exam_filter)
    results = results.order_by('exam_name', 'subject__subject_name')

    if request.method == 'POST':
        action = request.POST.get('form_action')
        admin_id = request.session.get('admin_id')
        admin = get_object_or_404(Admin, pk=admin_id)

        if action == 'update_marks':
            # Batch update marks and status for all results on page
            updated_count = 0
            for res in results:
                marks_key = f"marks_{res.id}"
                total_key = f"total_{res.id}"
                status_key = f"status_{res.id}"
                remarks_key = f"remarks_{res.id}"

                if marks_key in request.POST:
                    try:
                        m_obt = Decimal(str(request.POST.get(marks_key, res.marks_obtained)))
                        m_tot = Decimal(str(request.POST.get(total_key, res.total_marks)))
                        new_status = request.POST.get(status_key, res.verification_status)
                        new_remarks = request.POST.get(remarks_key, res.verification_remarks)

                        res.marks_obtained = m_obt
                        res.total_marks = m_tot
                        res.verification_status = new_status
                        res.verification_remarks = new_remarks
                        res.verified_by = admin
                        res.verification_date = timezone.now()
                        res.save()
                        updated_count += 1
                    except Exception:
                        pass

            messages.success(request, f'Successfully updated results and marks for {student.name}')
            return redirect('admin_student_results_manage', student_id=student.id)

        elif action == 'add_subject_result':
            # Add a single new subject result for this student
            subject_id = request.POST.get('new_subject_id')
            exam_name = request.POST.get('new_exam_name')
            marks_obt = request.POST.get('new_marks_obtained')
            total_marks = request.POST.get('new_total_marks', 100)
            status = request.POST.get('new_status', 'Verified')

            if subject_id and exam_name and marks_obt:
                try:
                    subject = get_object_or_404(Subject, pk=subject_id)
                    d_marks_obt = Decimal(str(marks_obt))
                    d_total_marks = Decimal(str(total_marks))

                    Result.objects.create(
                        student=student,
                        subject=subject,
                        exam_name=exam_name,
                        marks_obtained=d_marks_obt,
                        total_marks=d_total_marks,
                        verification_status=status,
                        verified_by=admin,
                        verification_date=timezone.now(),
                        exam_date=timezone.now().date()
                    )
                    messages.success(request, f'Added {subject.subject_name} result for {student.name}')
                except Exception as e:
                    messages.error(request, f'Error adding subject result: {str(e)}')
            else:
                messages.error(request, 'Please fill in all required fields to add subject result')

            return redirect('admin_student_results_manage', student_id=student.id)

        elif action == 'delete_result':
            result_id = request.POST.get('result_id')
            if result_id:
                res = get_object_or_404(Result, pk=result_id, student=student)
                res.delete()
                messages.success(request, 'Subject result deleted successfully')
            return redirect('admin_student_results_manage', student_id=student.id)

    subjects = Subject.objects.all().order_by('subject_name')
    exam_terms = ExamTerm.objects.filter(is_active=True).order_by('name')

    context = {
        'student': student,
        'results': results,
        'subjects': subjects,
        'exam_terms': exam_terms,
        'selected_exam': exam_filter,
    }
    return render(request, 'admin_portal/student_result_manage.html', context)


def result_approve(request, pk):
    """Admin approve a single result"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    admin_id = request.session.get('admin_id')
    admin = get_object_or_404(Admin, pk=admin_id)
    result = get_object_or_404(Result, pk=pk)
    
    result.verification_status = 'Verified'
    result.verified_by = admin
    result.verification_date = timezone.now()
    result.verification_remarks = request.POST.get('remarks', '')
    result.save()
    
    messages.success(request, f'Result for {result.student.name} - {result.subject.subject_name} approved')
    redirect_url = request.META.get('HTTP_REFERER') or reverse('result_verify')
    return redirect(redirect_url)


def result_reject(request, pk):
    """Admin reject a single result"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    admin_id = request.session.get('admin_id')
    admin = get_object_or_404(Admin, pk=admin_id)
    result = get_object_or_404(Result, pk=pk)
    
    result.verification_status = 'Rejected'
    result.verified_by = admin
    result.verification_date = timezone.now()
    result.verification_remarks = request.POST.get('remarks', 'Rejected by admin')
    result.save()
    
    messages.warning(request, f'Result for {result.student.name} - {result.subject.subject_name} rejected')
    redirect_url = request.META.get('HTTP_REFERER') or reverse('result_verify')
    return redirect(redirect_url)


def result_delete(request, pk):
    """Admin delete a result"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    result = get_object_or_404(Result, pk=pk)
    student_name = result.student.name
    result.delete()
    
    messages.success(request, f'Result for {student_name} deleted')
    return redirect('result_verify')


# ===================== RESULT PDF DOWNLOAD (Teacher Portal) =====================

def result_download(request):
    """Teacher view to select student and exam for result PDF download"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    # Get students based on teacher's class or all students
    if teacher.class_section.exists():
        students = Student.objects.filter(student_class__in=teacher.class_section.all(), is_active=True)
    else:
        students = Student.objects.filter(is_active=True)
    
    # Get distinct exam names from active ExamTerms
    exam_names = ExamTerm.objects.filter(is_active=True).values_list('name', flat=True)
    
    # Get actual SchoolClass objects for better filtering
    classes = SchoolClass.objects.all().order_by('class_name', 'section')
    
    context = {
        'teacher': teacher,
        'students': students,
        'exam_names': exam_names,
        'classes': classes,
    }
    return render(request, 'teacher/result_download.html', context)


# ===================== COMPLAINT MANAGEMENT =====================

def student_complaints(request):
    """Student view to list and submit complaints"""
    if request.session.get('user_type') != 'student':
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    student = get_object_or_404(Student, pk=student_id)
    
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.student = student
            complaint.save()
            messages.success(request, 'Complaint submitted successfully')
            return redirect('student_complaints')
    else:
        form = ComplaintForm()
    
    complaints = Complaint.objects.filter(student=student).order_by('-created_at')
    
    context = {
        'student': student,
        'complaints': complaints,
        'form': form
    }
    return render(request, 'student/complaints.html', context)


def admin_complaint_list(request):
    """Admin view to see all student complaints"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    complaints = Complaint.objects.all().select_related('student', 'student__student_class')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    
    context = {
        'complaints': complaints,
        'selected_status': status_filter
    }
    return render(request, 'admin_portal/complaint_list.html', context)


def admin_complaint_resolve(request, pk):
    """Admin view to resolve a complaint"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    complaint = get_object_or_404(Complaint, pk=pk)
    
    if request.method == 'POST':
        form = ComplaintResolveForm(request.POST, instance=complaint)
        if form.is_valid():
            complaint = form.save(commit=False)
            if complaint.status in ['Resolved', 'Closed'] and not complaint.resolved_at:
                complaint.resolved_at = timezone.now()
            complaint.save()
            messages.success(request, 'Complaint status updated successfully')
            return redirect('admin_complaint_list')
    else:
        form = ComplaintResolveForm(instance=complaint)
    
    context = {
        'complaint': complaint,
        'form': form
    }
    return render(request, 'admin_portal/complaint_resolve.html', context)


def admin_inquiry_list(request):
    """Admin view to see public inquiries"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    inquiries = Inquiry.objects.all()
    
    # Mark all as read when admin visits
    inquiries.filter(is_read=False).update(is_read=True)
    
    context = {
        'inquiries': inquiries
    }
    return render(request, 'admin_portal/inquiry_list.html', context)


def admin_inquiry_delete(request, pk):
    """Admin view to delete an inquiry"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    inquiry = get_object_or_404(Inquiry, pk=pk)
    inquiry.delete()
    messages.success(request, 'Inquiry deleted successfully')
    return redirect('admin_inquiry_list')


def result_pdf(request, student_id):
    """Generate printable result PDF for a student - accessible by admin, teacher, and student"""
    user_type = request.session.get('user_type')
    
    # Permission check
    if user_type == 'student':
        # Students can only view their own result
        session_student_id = request.session.get('student_id')
        if int(student_id) != int(session_student_id):
            messages.error(request, 'Permission denied')
            return redirect('student_dashboard')
    elif user_type not in ('admin', 'teacher'):
        # Must be logged in
        return redirect('student_login')
    
    student = get_object_or_404(Student, pk=student_id)
    exam_name = request.GET.get('exam', '')
    
    # Get all verified results for this student and exam
    results = Result.objects.filter(
        student=student,
        exam_name=exam_name,
        verification_status='Verified'
    ).select_related('subject').order_by('subject__subject_name')
    
    # Calculate overall totals
    total_marks_obtained = sum(r.marks_obtained for r in results)
    total_marks_total = sum(r.total_marks for r in results)
    overall_percentage = (total_marks_obtained / total_marks_total * 100) if total_marks_total > 0 else 0
    
    # Use GradeConfig for grade calculation
    grade_config = GradeConfig.get_config()
    overall_grade = grade_config.get_grade(overall_percentage)
    result_status = 'PASS' if overall_percentage >= grade_config.pass_percentage else 'FAIL'
    
    school_info = SchoolInfo.objects.first()
    
    context = {
        'student': student,
        'exam_name': exam_name,
        'results': results,
        'total_marks_obtained': total_marks_obtained,
        'total_marks_total': total_marks_total,
        'overall_percentage': overall_percentage,
        'overall_grade': overall_grade,
        'result_status': result_status,
        'total_subjects': results.count(),
        'school_info': school_info,
        'grade_config': grade_config,
    }
    return render(request, 'public_result_card.html', context)


def fee_receipt_pdf(request, payment_id):
    """Generate printable fee receipt PDF"""
    # Permission check: Admin or the student who made the payment
    user_type = request.session.get('user_type')
    student_id = request.session.get('student_id')
    
    payment = get_object_or_404(StudentPayment, pk=payment_id)
    
    if user_type == 'admin':
        # Admin can view any receipt
        pass
    elif user_type == 'student' and student_id == payment.student_id:
        # Student can only view their own receipt
        pass
    else:
        messages.error(request, 'Permission denied')
        return redirect('home')
        
    context = {
        'payment': payment,
    }
    return render(request, 'student/fee_receipt_pdf.html', context)


# ===================== GALLERY MANAGEMENT =====================

def gallery_list(request):
    """Admin view to manage gallery images"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    images = GalleryImage.objects.all().order_by('-display_order', '-upload_date')
    
    context = {
        'images': images,
    }
    return render(request, 'admin_portal/gallery_list.html', context)


def gallery_add(request):
    """Admin add gallery image"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category')
        description = request.POST.get('description', '')
        image = request.FILES.get('image')
        display_order = request.POST.get('display_order', 0)
        
        if title and image:
            GalleryImage.objects.create(
                title=title,
                category=category,
                description=description,
                image=image.read(),
                image_mimetype=image.content_type,
                image_filename=image.name,
                display_order=int(display_order) if display_order else 0
            )
            messages.success(request, 'Gallery image added successfully')
        else:
            messages.error(request, 'Title and image are required')
        
        return redirect('gallery_list')
    
    return redirect('gallery_list')


def gallery_delete(request, pk):
    """Admin delete gallery image"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    image = get_object_or_404(GalleryImage, pk=pk)
    image.delete()
    
    messages.success(request, 'Gallery image deleted')
    return redirect('gallery_list')


# ===================== BINARY FILE SERVING =====================

def serve_binary(request, model_name, record_id, field_name):
    """View to serve binary data from any model specifically for this project.
    If the record has a photo_url (for photo fields), redirect to that URL instead."""
    try:
        model = apps.get_model('core', model_name)
        record = get_object_or_404(model, pk=record_id)

        # If serving a photo field and photo_url is set, redirect to external URL
        if field_name == 'photo' and hasattr(record, 'photo_url') and record.photo_url:
            from django.shortcuts import redirect as django_redirect
            return django_redirect(record.photo_url)

        # Get binary data
        binary_data = getattr(record, field_name, None)
        if not binary_data:
            raise Http404("File not found")
        
        # Get metadata
        mimetype = getattr(record, f"{field_name}_mimetype", "application/octet-stream")
        filename = getattr(record, f"{field_name}_filename", f"{model_name}_{record_id}")
        
        response = HttpResponse(binary_data, content_type=mimetype)
        # Only set attachment for non-images or if explicitly requested
        if 'image' not in mimetype:
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    except Exception as e:
        raise Http404(f"Error serving file: {str(e)}")

# ===================== HEALTH CHECK =====================

def health_check(request):
    """Render and UptimeRobot health check endpoint"""
    return HttpResponse("OK", status=200)

# ===================== ADMIT CARD (ADMIN) =====================

def admin_admit_card_list(request):
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    requests = AdmitCardRequest.objects.all().order_by('-created_at')
    return render(request, 'admin_portal/admit_card_request_list.html', {'requests': requests})

def admin_admit_card_issue(request):
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
        
    if request.method == 'POST':
        class_id = request.POST.get('school_class')
        term_id = request.POST.get('exam_term')
        
        try:
            school_class = SchoolClass.objects.get(pk=class_id)
            exam_term = ExamTerm.objects.get(pk=term_id)
            admin = Admin.objects.get(pk=request.session.get('admin_id'))
            
            if AdmitCardRequest.objects.filter(school_class=school_class, exam_term=exam_term).exists():
                messages.error(request, 'An admit card request for this class and exam term already exists.')
            else:
                AdmitCardRequest.objects.create(
                    school_class=school_class,
                    exam_term=exam_term,
                    created_by=admin
                )
                messages.success(request, 'Admit card request issued successfully. Waiting for class teacher to schedule it.')
                return redirect('admin_admit_card_list')
        except Exception as e:
            messages.error(request, f'Error issuing admit card: {str(e)}')
            
    classes = SchoolClass.objects.all()
    terms = ExamTerm.objects.filter(is_active=True)
    return render(request, 'admin_portal/admit_card_request_form.html', {'classes': classes, 'terms': terms})

def admin_admit_card_delete(request, pk):
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
        
    ac_request = get_object_or_404(AdmitCardRequest, pk=pk)
    ac_request.delete()
    messages.success(request, 'Admit card request deleted successfully.')
    return redirect('admin_admit_card_list')

# ===================== ADMIT CARD (TEACHER) =====================

def teacher_admit_card_requests(request):
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
        
    teacher = Teacher.objects.get(pk=request.session.get('teacher_id'))
    if teacher.class_section.exists():
        requests = AdmitCardRequest.objects.filter(school_class__in=teacher.class_section.all()).order_by('-created_at')
    else:
        requests = []
        
    return render(request, 'teacher/admit_card_requests.html', {'requests': requests, 'teacher': teacher})

def teacher_admit_card_schedule(request, request_id):
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
        
    ac_request = get_object_or_404(AdmitCardRequest, pk=request_id)
    teacher = Teacher.objects.get(pk=request.session.get('teacher_id'))
    
    if not teacher.class_section.filter(pk=ac_request.school_class.pk).exists():
        messages.error(request, 'You can only schedule exams for your own class.')
        return redirect('teacher_admit_card_requests')
        
    if request.method == 'POST':
        subject_ids = request.POST.getlist('subject[]')
        dates = request.POST.getlist('exam_date[]')
        start_times = request.POST.getlist('start_time[]')
        end_times = request.POST.getlist('end_time[]')
        
        try:
            ExamSchedule.objects.filter(admit_card_request=ac_request).delete()
            
            for i in range(len(subject_ids)):
                if subject_ids[i] and dates[i] and start_times[i] and end_times[i]:
                    ExamSchedule.objects.create(
                        admit_card_request=ac_request,
                        subject_id=subject_ids[i],
                        exam_date=dates[i],
                        start_time=start_times[i],
                        end_time=end_times[i]
                    )
                    
            ac_request.is_published = True
            ac_request.save()
            
            messages.success(request, 'Exam schedule published successfully. Students can now download their admit cards.')
            return redirect('teacher_admit_card_requests')
        except Exception as e:
            messages.error(request, f'Error saving schedule: {str(e)}')
            
    schedules = ExamSchedule.objects.filter(admit_card_request=ac_request)
    subjects = Subject.objects.all()
    
    return render(request, 'teacher/admit_card_schedule_form.html', {
        'ac_request': ac_request,
        'schedules': schedules,
        'subjects': subjects,
        'teacher': teacher
    })

# ===================== ADMIT CARD (PUBLIC) =====================

def public_admit_card_search(request):
    school_info = SchoolInfo.objects.first()
    classes = SchoolClass.objects.all()
    
    student_id_raw = request.GET.get('student_id')
    class_id = request.GET.get('class_id')
    
    if student_id_raw and class_id:
        student_id_str = student_id_raw.strip().upper()
        if student_id_str.startswith('MPS-'):
            student_id_str = student_id_str[4:]
            
        try:
            student_pk = int(student_id_str)
            student = Student.objects.get(pk=student_pk, student_class_id=class_id, is_active=True)
            
            ac_requests = AdmitCardRequest.objects.filter(school_class_id=class_id, is_published=True).order_by('-created_at')
            
            if not ac_requests.exists():
                return render(request, 'admit_card_search.html', {
                    'classes': classes,
                    'error': 'No admit card published for this class yet.',
                    'school_info': school_info
                })
                
            ac_request = ac_requests.first()
            schedules = ExamSchedule.objects.filter(admit_card_request=ac_request).order_by('exam_date', 'start_time')
            
            return render(request, 'public_admit_card.html', {
                'student': student,
                'ac_request': ac_request,
                'schedules': schedules,
                'school_info': school_info
            })
            
        except (ValueError, Student.DoesNotExist):
            return render(request, 'admit_card_search.html', {
                'classes': classes,
                'error': 'Invalid Student ID or Class combination.',
                'school_info': school_info
            })
            
    return render(request, 'admit_card_search.html', {'classes': classes, 'school_info': school_info})


# ===================== STUDENT RESULT DOWNLOAD =====================

def student_result_page(request):
    """Student portal - view and download results"""
    if request.session.get('user_type') != 'student':
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    student = get_object_or_404(Student, pk=student_id)
    
    # Get distinct exam names for this student's verified results
    exam_names = Result.objects.filter(
        student=student,
        verification_status='Verified'
    ).values_list('exam_name', flat=True).distinct().order_by('exam_name')
    
    selected_exam = request.GET.get('exam', '')
    results = []
    total_marks_obtained = 0
    total_marks_total = 0
    overall_percentage = 0
    overall_grade = '-'
    result_status = '-'
    grade_config = GradeConfig.get_config()
    
    if selected_exam:
        results = Result.objects.filter(
            student=student,
            exam_name=selected_exam,
            verification_status='Verified'
        ).select_related('subject').order_by('subject__subject_name')
        
        if results.exists():
            total_marks_obtained = sum(r.marks_obtained for r in results)
            total_marks_total = sum(r.total_marks for r in results)
            overall_percentage = float((total_marks_obtained / total_marks_total * 100) if total_marks_total > 0 else 0)
            overall_grade = grade_config.get_grade(overall_percentage)
            result_status = 'PASS' if overall_percentage >= grade_config.pass_percentage else 'FAIL'
    
    context = {
        'student': student,
        'exam_names': exam_names,
        'selected_exam': selected_exam,
        'results': results,
        'total_marks_obtained': total_marks_obtained,
        'total_marks_total': total_marks_total,
        'overall_percentage': overall_percentage,
        'overall_grade': overall_grade,
        'result_status': result_status,
        'total_subjects': len(results) if results else 0,
        'grade_config': grade_config,
        'school_info': SchoolInfo.objects.first(),
    }
    return render(request, 'student/result_page.html', context)


# ===================== ADMIN GRADE CONFIG =====================

def admin_grade_config(request):
    """Admin view to configure grade percentage criteria"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    config = GradeConfig.get_config()
    
    if request.method == 'POST':
        try:
            config.a_plus_min = int(request.POST.get('a_plus_min', 90))
            config.a_min = int(request.POST.get('a_min', 80))
            config.b_plus_min = int(request.POST.get('b_plus_min', 70))
            config.b_min = int(request.POST.get('b_min', 60))
            config.c_min = int(request.POST.get('c_min', 50))
            config.d_min = int(request.POST.get('d_min', 40))
            config.pass_percentage = int(request.POST.get('pass_percentage', 40))
            config.save()
            messages.success(request, 'Grade criteria updated successfully!')
            return redirect('admin_grade_config')
        except Exception as e:
            messages.error(request, f'Error updating grade config: {str(e)}')
    
    return render(request, 'admin_portal/grade_config.html', {'config': config})


# ===================== ADMIN STUDENT REGISTRATION PDF =====================

def admin_student_registration_pdf(request, student_id):
    """Admin view to generate professional registration PDF for a student"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    student = get_object_or_404(Student, pk=student_id)
    school_info = SchoolInfo.objects.first()
    
    student_password = student.raw_password if (hasattr(student, 'raw_password') and student.raw_password) else 'student123'
    
    context = {
        'student': student,
        'school_info': school_info,
        'student_code': f'MPS-{student.pk:04d}',
        'login_email': student.email if student.email else f'student{student.pk}@midpoint.edu',
        'raw_password': student_password,
    }
    return render(request, 'admin_portal/student_registration_pdf.html', context)
