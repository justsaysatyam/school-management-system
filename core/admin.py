from django.contrib import admin
from .models import (
    SchoolClass, Subject, Admin, Teacher, Student,
    TeacherPayment, StudentPayment, TeacherAttendance, StudentAttendance,
    Notice, Event, Exam
)


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    #hii hello byy
    list_display = ['class_name', 'section', 'strength']
    list_filter = ['class_name']
    search_fields = ['class_name', 'section']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['subject_name', 'subject_code']
    search_fields = ['subject_name', 'subject_code']


@admin.register(Admin)
class AdminModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'role']
    search_fields = ['name', 'email']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'mobile', 'qualification', 'monthly_salary', 'is_active']
    list_filter = ['is_active', 'qualification', 'class_section']
    search_fields = ['name', 'email', 'mobile']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'father_name', 'student_class', 'mobile', 'monthly_fee', 'is_active']
    list_filter = ['is_active', 'student_class']
    search_fields = ['name', 'father_name', 'mobile']


@admin.register(TeacherPayment)
class TeacherPaymentAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'month', 'year', 'paid_amount', 'due_amount', 'status', 'payment_date']
    list_filter = ['status', 'month', 'year']
    search_fields = ['teacher__name']


@admin.register(StudentPayment)
class StudentPaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'month', 'year', 'paid_amount', 'due_amount', 'status', 'payment_date']
    list_filter = ['status', 'month', 'year']
    search_fields = ['student__name']


@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'date', 'status']
    list_filter = ['status', 'date']
    search_fields = ['teacher__name']


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status']
    list_filter = ['status', 'date']
    search_fields = ['student__name']


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'priority', 'audience', 'notice_date', 'is_active']
    list_filter = ['category', 'priority', 'audience', 'is_active']
    search_fields = ['title', 'description']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_date', 'event_time', 'is_active']
    list_filter = ['is_active', 'event_date']
    search_fields = ['title']


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['exam_name', 'school_class', 'subject', 'exam_date', 'exam_time', 'room_no']
    list_filter = ['school_class', 'exam_date']
    search_fields = ['exam_name']
