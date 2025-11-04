from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

app_name = 'exam'

urlpatterns = [
    # ===== AUTHENTICATION & REDIRECT =====
    path('', views.login_redirect, name='home'),
    
    path('login/', auth_views.LoginView.as_view(template_name='exam/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),

    # ===== STUDENT ROUTES =====
    path('student/my-exams/', views.my_exams, name='my_exams'),
    path('student/exam/<int:exam_id>/', views.take_exam, name='take_exam'),
    path('exam/<int:exam_id>/take/', views.take_exam, name='take_exam'),
    path('exam/<int:exam_id>/submit/', views.submit_exam, name='submit_exam'),
    path('results/<int:session_id>/', views.exam_results, name='exam_results'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/exam-token/', views.exam_token_access, name='exam_token_access'),
    path('api/validate-token/', views.validate_exam_token, name='validate_exam_token'),
    path('student/validate-token/', views.validate_exam_token, name='validate_exam_token'),
    path('student/exam/token/<str:token>/', views.access_exam_with_token, name='access_exam_with_token'),

    path('student/results/', views.student_results, name='student_results'),
    path('student/results/<int:session_id>/', views.student_result_detail, name='student_result_detail'),


     # Error pages
    path('exam/not-available/', views.exam_not_available, name='exam_not_available'),
    path('exam/ended/', views.exam_ended, name='exam_ended'),
    path('exam/access-denied/', views.exam_access_denied, name='exam_access_denied'),
    

    # ===== TEACHER ROUTES =====
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/simple-dashboard/', views.simple_teacher_dashboard, name='simple_teacher_dashboard'),
    path('teacher/questions/', views.teacher_questions, name='teacher_questions'),
    path('teacher/questions/add/', views.add_question, name='add_question'),
    path('teacher/questions/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('teacher/questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('teacher/questions/bulk-upload/', views.bulk_upload_questions, name='bulk_upload_questions'),
    path('teacher/question-banks/create/', views.create_question_bank, name='create_question_bank'),
    path('teacher/question-banks/<int:bank_id>/', views.question_bank_detail, name='question_bank_detail'),
    path('teacher/add-question/', views.add_question, name='add_question'),
    path('questions/bulk-upload/', views.bulk_upload_questions, name='bulk_upload_questions'),
    path('question-banks/download-template/', views.download_question_bank_template, name='download_question_bank_template'),
    path('download-template/', views.download_question_bank_template, name='download_question_bank_template'),
    path('teacher/exams/create/', views.create_exam, name='create_exam'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),






    # ===== ADMIN ROUTES =====
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/stats/', views.admin_stats, name='admin_stats'),
    path('admin/user-management/', views.user_management, name='user_management'),
   
    # ===== FALLBACK REDIRECTS =====
    path('dashboard/', views.login_redirect, name='dashboard_redirect'),
    path('teacher/', lambda request: redirect('exam:teacher_dashboard')),
    path('student/', lambda request: redirect('exam:my-exams')),
    path('admin/', lambda request: redirect('exam:admin_dashboard')),


]