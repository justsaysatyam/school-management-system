from django.urls import path
from . import views

urlpatterns = [
    # Home and Authentication
    path('', views.home, name='home'),
    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-verify-otp/', views.admin_verify_otp, name='admin_verify_otp'),
    path('admin-resend-otp/', views.admin_resend_otp, name='admin_resend_otp'),
    path('admin-register-telegram/', views.admin_register_telegram, name='admin_register_telegram'),
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
    path('admin/students/<int:student_id>/registration-pdf/', views.admin_student_registration_pdf, name='admin_student_registration_pdf'),
    path('admin/teachers/<int:pk>/id-card/', views.teacher_id_card, name='teacher_id_card'),
    
    # Teacher Management (Admin)
    path('admin/teachers/', views.teacher_list, name='teacher_list'),
    path('admin/teachers/add/', views.teacher_add, name='teacher_add'),
    path('admin/teachers/<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('admin/teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    
    # Fee Management (Admin)
    path('admin/fees/', views.fee_collection, name='fee_collection'),
    path('admin/fees/add/', views.fee_add, name='fee_add'),
    path('admin/fees/<int:pk>/edit/', views.fee_edit, name='fee_edit'),
    path('fee/receipt/<int:payment_id>/', views.fee_receipt_pdf, name='fee_receipt_pdf'),
    path('admin/api/students-by-class/', views.admin_get_students_by_class, name='admin_get_students_by_class'),
    
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
    
    # Subject Management (Admin)
    path('admin/subjects/', views.subject_list, name='subject_list'),
    path('admin/subjects/add/', views.subject_add, name='subject_add'),
    path('admin/subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    
    # Exam Term Management (Admin)
    path('admin/exam-terms/', views.exam_term_list, name='exam_term_list'),
    path('admin/exam-terms/add/', views.exam_term_add, name='exam_term_add'),
    path('admin/exam-terms/<int:pk>/edit/', views.exam_term_edit, name='exam_term_edit'),
    path('admin/exam-terms/<int:pk>/delete/', views.exam_term_delete, name='exam_term_delete'),
    
    # Teacher Attendance Management (Admin)
    path('admin/teacher-attendance/', views.teacher_attendance_list, name='teacher_attendance_list'),
    path('admin/teacher-attendance/mark/', views.teacher_attendance_mark, name='teacher_attendance_mark'),
    
    # Student Portal
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/payments/', views.student_payment_history, name='student_payment_history'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/results/', views.student_result_page, name='student_result_page'),
    path('student/results/pdf/<int:student_id>/', views.result_pdf, name='student_result_pdf'),
    
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
    path('teacher/api/students-by-class/', views.teacher_get_students_by_class, name='teacher_get_students_by_class'),
    path('teacher/results/<int:pk>/edit/', views.result_edit, name='result_edit'),
    path('admin/results/verify/', views.result_verify, name='result_verify'),
    path('admin/results/verify-student/', views.result_verify_student_all, name='result_verify_student_all'),
    path('admin/results/verify-bulk/', views.result_verify_bulk, name='result_verify_bulk'),
    path('admin/results/student/<int:student_id>/manage/', views.admin_student_results_manage, name='admin_student_results_manage'),
    path('admin/results/<int:pk>/approve/', views.result_approve, name='result_approve'),
    path('admin/results/<int:pk>/reject/', views.result_reject, name='result_reject'),
    path('admin/results/<int:pk>/delete/', views.result_delete, name='result_delete'),
    
    # Result PDF Download (Teacher Portal)
    path('teacher/results/download/', views.result_download, name='result_download'),
    path('teacher/results/pdf/<int:student_id>/', views.result_pdf, name='teacher_result_pdf'),
    
    # Admit Card Management (Admin)
    path('admin/admit-cards/', views.admin_admit_card_list, name='admin_admit_card_list'),
    path('admin/admit-cards/issue/', views.admin_admit_card_issue, name='admin_admit_card_issue'),
    path('admin/admit-cards/<int:pk>/delete/', views.admin_admit_card_delete, name='admin_admit_card_delete'),
    
    # Admit Card Management (Teacher)
    path('teacher/admit-cards/', views.teacher_admit_card_requests, name='teacher_admit_card_requests'),
    path('teacher/admit-cards/<int:request_id>/schedule/', views.teacher_admit_card_schedule, name='teacher_admit_card_schedule'),
    
    # Admit Card (Public Portal)
    path('admit-card/', views.public_admit_card_search, name='public_admit_card_search'),
    
    # Gallery Management
    path('admin/gallery/', views.gallery_list, name='gallery_list'),
    path('admin/gallery/add/', views.gallery_add, name='gallery_add'),
    path('admin/gallery/<int:pk>/delete/', views.gallery_delete, name='gallery_delete'),
    
    # Complaint Management
    path('student/complaints/', views.student_complaints, name='student_complaints'),
    path('admin/complaints/', views.admin_complaint_list, name='admin_complaint_list'),
    path('admin/complaints/<int:pk>/resolve/', views.admin_complaint_resolve, name='admin_complaint_resolve'),
    
    # Inquiry Management
    path('admin/inquiries/', views.admin_inquiry_list, name='admin_inquiry_list'),
    path('admin/inquiries/<int:pk>/delete/', views.admin_inquiry_delete, name='admin_inquiry_delete'),
    
    # Binary Serving
    path('serve-binary/<str:model_name>/<int:record_id>/<str:field_name>/', views.serve_binary, name='serve_binary'),
    
    # Grade Configuration (Admin)
    path('admin/grade-config/', views.admin_grade_config, name='admin_grade_config'),
    
    # Health Check
    path('health-check/', views.health_check, name='health_check'),
]
