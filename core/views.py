from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from decimal import Decimal
from .models import (
    Admin, Teacher, Student, SchoolClass, Subject,
    TeacherPayment, StudentPayment, TeacherAttendance, StudentAttendance,
    Notice, Event, Exam, SchoolInfo, GalleryImage, Result
)
from .forms import (
    LoginForm, TeacherForm, StudentForm, TeacherPaymentForm, 
    StudentPaymentForm, NoticeForm, ClassForm, SubjectForm
)


# ===================== HOME & AUTH =====================

def home(request):
    """Landing page with portfolio, login options, and results"""
    # Get or create school info
    school_info = SchoolInfo.objects.first()
    if not school_info:
        school_info = SchoolInfo.objects.create()
    
    # Get gallery images
    gallery_images = GalleryImage.objects.filter(is_active=True)[:8]
    
    context = {
        'school_info': school_info,
        'gallery_images': gallery_images,
    }
    return render(request, 'home.html', context)


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
            try:
                student = Student.objects.get(email=email, is_active=True)
                if student.check_password(password):
                    request.session['student_id'] = student.id
                    request.session['user_type'] = 'student'
                    request.session['user_name'] = student.name
                    return redirect('student_dashboard')
                else:
                    messages.error(request, 'Invalid password')
            except Student.DoesNotExist:
                messages.error(request, 'Student not found')
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
    """Generate printable student ID card"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'admin_portal/student_id_card.html', {'student': student})


# ===================== TEACHER MANAGEMENT =====================

def teacher_list(request):
    """List all teachers"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    teachers = Teacher.objects.all().select_related('class_section')
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
    """View all fee payments"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    payments = StudentPayment.objects.all().select_related('student')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        payments = payments.filter(status=status)
    
    context = {
        'payments': payments,
        'selected_status': status
    }
    return render(request, 'admin_portal/fee_collection.html', context)


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
    
    return render(request, 'admin_portal/fee_form.html', {'form': form, 'title': 'Record Fee Payment'})


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
    
    return render(request, 'admin_portal/fee_form.html', {'form': form, 'title': 'Edit Fee Payment'})


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
            'address': 'Barahiya, Ward No. 04, Lakhisarai, Bihar',
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
            'address': 'Barahiya, Ward No. 04, Lakhisarai, Bihar',
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
    if teacher.class_section:
        students = Student.objects.filter(student_class=teacher.class_section, is_active=True)
    
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
    """Teacher view of students"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    students = []
    if teacher.class_section:
        students = Student.objects.filter(student_class=teacher.class_section, is_active=True)
    
    return render(request, 'teacher/students.html', {'students': students, 'teacher': teacher})


def teacher_profile(request):
    """Teacher profile view"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    return render(request, 'teacher/profile.html', {'teacher': teacher})


# ===================== STUDENT ATTENDANCE (Teacher Portal) =====================

def student_attendance_list(request):
    """Teacher view to mark student attendance"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    from datetime import date
    
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    # Check if teacher has a class assigned
    if not teacher.class_section:
        messages.warning(request, 'You are not assigned to any class')
        return render(request, 'teacher/student_attendance.html', {
            'teacher': teacher,
            'students_with_attendance': [],
            'selected_date': date.today(),
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
    
    # Get all students in teacher's class
    students = Student.objects.filter(
        student_class=teacher.class_section, 
        is_active=True
    ).order_by('name')
    
    # Get attendance records for the selected date
    attendance_records = StudentAttendance.objects.filter(
        date=selected_date,
        student__student_class=teacher.class_section
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
        
        if not teacher.class_section:
            messages.error(request, 'You are not assigned to any class')
            return redirect('student_attendance_list')
        
        attendance_date = request.POST.get('attendance_date')
        try:
            attendance_date = date.fromisoformat(attendance_date)
        except (ValueError, TypeError):
            attendance_date = date.today()
        
        # Process attendance for each student in teacher's class
        students = Student.objects.filter(
            student_class=teacher.class_section,
            is_active=True
        )
        
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
        return redirect(f'/teacher/student-attendance/?date={attendance_date}')
    
    return redirect('student_attendance_list')


# ===================== RESULTS MANAGEMENT =====================

def result_list(request):
    """Public view of all verified results"""
    results = Result.objects.filter(verification_status='Verified').select_related(
        'student', 'subject', 'student__student_class', 'submitted_by'
    ).order_by('-exam_date', 'student__student_class', 'student__name')
    
    # Filter by class
    class_id = request.GET.get('class')
    selected_class_id = None
    if class_id:
        try:
            selected_class_id = int(class_id)
            results = results.filter(student__student_class_id=selected_class_id)
        except (ValueError, TypeError):
            pass
    
    # Filter by exam
    exam_name = request.GET.get('exam')
    if exam_name:
        results = results.filter(exam_name__icontains=exam_name)
    
    classes = SchoolClass.objects.all()
    exam_names = Result.objects.filter(verification_status='Verified').values_list('exam_name', flat=True).distinct()
    
    # Get students who have verified results (for PDF download section)
    students_with_results = Student.objects.filter(
        results__verification_status='Verified'
    ).distinct().order_by('student_class__class_name', 'name')
    
    context = {
        'results': results,
        'classes': classes,
        'exam_names': exam_names,
        'selected_class': selected_class_id,
        'selected_exam': exam_name,
        'students_with_results': students_with_results,
    }
    return render(request, 'result_list.html', context)


def result_submit(request):
    """Teacher view to submit student results"""
    if request.session.get('user_type') != 'teacher':
        return redirect('teacher_login')
    
    teacher_id = request.session.get('teacher_id')
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        exam_name = request.POST.get('exam_name')
        subject_id = request.POST.get('subject')
        marks_obtained = request.POST.get('marks_obtained')
        total_marks = request.POST.get('total_marks')
        exam_date = request.POST.get('exam_date')
        remarks = request.POST.get('remarks', '')
        
        try:
            student = Student.objects.get(pk=student_id)
            subject = Subject.objects.get(pk=subject_id) if subject_id else None
            
            result = Result.objects.create(
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
            
            messages.success(request, f'Result submitted successfully for {student.name}. Pending admin verification.')
            return redirect('result_submit')
        except Exception as e:
            messages.error(request, f'Error submitting result: {str(e)}')
    
    # Get students based on teacher's class or all students
    if teacher.class_section:
        students = Student.objects.filter(student_class=teacher.class_section, is_active=True)
    else:
        students = Student.objects.filter(is_active=True)
    
    subjects = Subject.objects.all()
    
    # Get teacher's submitted results
    submitted_results = Result.objects.filter(submitted_by=teacher).select_related(
        'student', 'subject'
    ).order_by('-submission_date')[:20]
    
    context = {
        'teacher': teacher,
        'students': students,
        'subjects': subjects,
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


def result_verify(request):
    """Admin view to verify submitted results"""
    if request.session.get('user_type') != 'admin':
        return redirect('admin_login')
    
    admin_id = request.session.get('admin_id')
    
    # Get pending results
    pending_results = Result.objects.filter(verification_status='Pending').select_related(
        'student', 'subject', 'submitted_by', 'student__student_class'
    ).order_by('-submission_date')
    
    # Get recently verified/rejected results
    recent_results = Result.objects.filter(
        verification_status__in=['Verified', 'Rejected']
    ).select_related(
        'student', 'subject', 'submitted_by', 'verified_by'
    ).order_by('-verification_date')[:20]
    
    context = {
        'pending_results': pending_results,
        'recent_results': recent_results,
    }
    return render(request, 'admin_portal/result_verify.html', context)


def result_approve(request, pk):
    """Admin approve a result"""
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
    
    messages.success(request, f'Result for {result.student.name} - {result.exam_name} approved')
    return redirect('result_verify')


def result_reject(request, pk):
    """Admin reject a result"""
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
    
    messages.warning(request, f'Result for {result.student.name} - {result.exam_name} rejected')
    return redirect('result_verify')


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
    if teacher.class_section:
        students = Student.objects.filter(student_class=teacher.class_section, is_active=True)
    else:
        students = Student.objects.filter(is_active=True)
    
    # Get distinct exam names from verified results
    exam_names = Result.objects.filter(
        verification_status='Verified'
    ).values_list('exam_name', flat=True).distinct()
    
    # Get actual SchoolClass objects for better filtering
    classes = SchoolClass.objects.all().order_by('class_name', 'section')
    
    context = {
        'teacher': teacher,
        'students': students,
        'exam_names': exam_names,
        'classes': classes,
    }
    return render(request, 'teacher/result_download.html', context)


def result_pdf(request, student_id):
    """Generate printable result PDF for a student - public access"""
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
    
    # Calculate overall grade
    if overall_percentage >= 90:
        overall_grade = 'A+'
    elif overall_percentage >= 80:
        overall_grade = 'A'
    elif overall_percentage >= 70:
        overall_grade = 'B+'
    elif overall_percentage >= 60:
        overall_grade = 'B'
    elif overall_percentage >= 50:
        overall_grade = 'C'
    elif overall_percentage >= 40:
        overall_grade = 'D'
    else:
        overall_grade = 'F'
    
    # Determine pass/fail status
    result_status = 'PASS' if overall_percentage >= 40 else 'FAIL'
    
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
    }
    return render(request, 'teacher/student_result_pdf.html', context)


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
                image=image,
                display_order=int(display_order)
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
