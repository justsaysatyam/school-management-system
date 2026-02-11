from django.urls import path
from . import views

urlpatterns = [
    # Home and Authentication
    path('', views.home, name='home'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('teacher-login/', views.teacher_login, name='teacher_login'),
    path('student-login/', views.student_login, name='student_login'),
    path('logout/', views.logout, name='logout'),
    
    # Admin Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Student Management (Admin)
    path('admin/students/', views.student_list, name='student_list'),
    path('admin/students/add/', views.student_add, name='student_add'),
    path('admin/students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('admin/students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('admin/students/<int:pk>/id-card/', views.student_id_card, name='student_id_card'),
    
    # Teacher Management (Admin)
    path('admin/teachers/', views.teacher_list, name='teacher_list'),
    path('admin/teachers/add/', views.teacher_add, name='teacher_add'),
    path('admin/teachers/<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('admin/teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    
    # Fee Management (Admin)
    path('admin/fees/', views.fee_collection, name='fee_collection'),
    path('admin/fees/add/', views.fee_add, name='fee_add'),
    path('admin/fees/<int:pk>/edit/', views.fee_edit, name='fee_edit'),
    
    # Salary Management (Admin)
    path('admin/salaries/', views.salary_management, name='salary_management'),
    path('admin/salaries/add/', views.salary_add, name='salary_add'),
    path('admin/salaries/<int:pk>/edit/', views.salary_edit, name='salary_edit'),
    
    # Notice Management (Admin)
    path('admin/notices/', views.notice_list, name='notice_list'),
    path('admin/notices/add/', views.notice_add, name='notice_add'),
    path('admin/notices/<int:pk>/delete/', views.notice_delete, name='notice_delete'),
    
    # Class Management (Admin)
    path('admin/classes/', views.class_list, name='class_list'),
    path('admin/classes/add/', views.class_add, name='class_add'),
    path('admin/classes/<int:pk>/delete/', views.class_delete, name='class_delete'),
    
    # Teacher Attendance Management (Admin)
    path('admin/teacher-attendance/', views.teacher_attendance_list, name='teacher_attendance_list'),
    path('admin/teacher-attendance/mark/', views.teacher_attendance_mark, name='teacher_attendance_mark'),
    
    # Student Portal
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/payments/', views.student_payment_history, name='student_payment_history'),
    path('student/profile/', views.student_profile, name='student_profile'),
    
    # Teacher Portal
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/salary/', views.teacher_salary_history, name='teacher_salary_history'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/profile/', views.teacher_profile, name='teacher_profile'),
    path('teacher/student-attendance/', views.student_attendance_list, name='student_attendance_list'),
    path('teacher/student-attendance/mark/', views.student_attendance_mark, name='student_attendance_mark'),
    
    # Results Management
    path('results/', views.result_list, name='result_list'),
    path('results/pdf/<int:student_id>/', views.result_pdf, name='result_pdf'),
    path('teacher/results/submit/', views.result_submit, name='result_submit'),
    path('teacher/results/<int:pk>/edit/', views.result_edit, name='result_edit'),
    path('admin/results/verify/', views.result_verify, name='result_verify'),
    path('admin/results/<int:pk>/approve/', views.result_approve, name='result_approve'),
    path('admin/results/<int:pk>/reject/', views.result_reject, name='result_reject'),
    path('admin/results/<int:pk>/delete/', views.result_delete, name='result_delete'),
    
    # Result PDF Download (Teacher Portal)
    path('teacher/results/download/', views.result_download, name='result_download'),
    path('teacher/results/pdf/<int:student_id>/', views.result_pdf, name='teacher_result_pdf'),
    
    # Gallery Management
    path('admin/gallery/', views.gallery_list, name='gallery_list'),
    path('admin/gallery/add/', views.gallery_add, name='gallery_add'),
    path('admin/gallery/<int:pk>/delete/', views.gallery_delete, name='gallery_delete'),
]
