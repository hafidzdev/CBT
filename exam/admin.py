from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.db.models import Avg
from django.utils import timezone
from django.contrib.admin import SimpleListFilter
from datetime import timedelta

from .models import (
    CustomUser,
    Department,
    Subject,
    Exam,
    Question,
    ExamSession,
    QuestionBank,
    UserAnswer,
    ProctoringEvent,
    Certificate,
    SystemLog,
    Choice
)

# =========================
# CUSTOM ADMIN SITE
# =========================
class CustomAdminSite(admin.AdminSite):
    site_header = "CBT System Administration"
    site_title = "CBT System Admin"
    index_title = "Dashboard"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('admin-stats/', self.admin_view(self.admin_stats), name='admin-stats'),
            path('user-management/', self.admin_view(self.user_management), name='user-management'),
        ]
        return custom_urls + urls
    
    def admin_stats(self, request):
        """Custom Dashboard Stats"""
        total_users = CustomUser.objects.count()
        total_exams = Exam.objects.count()
        total_sessions = ExamSession.objects.count()
        active_sessions = ExamSession.objects.filter(status='in_progress').count()

        recent_exams = Exam.objects.order_by('-created_at')[:5]
        recent_sessions = ExamSession.objects.select_related('user', 'exam').order_by('-start_time')[:10]

        avg_score = ExamSession.objects.filter(score__isnull=False).aggregate(Avg('score'))['score__avg'] or 0
        pass_rate = (ExamSession.objects.filter(score__gte=60).count() / total_sessions * 100) if total_sessions > 0 else 0

        context = {
            'total_users': total_users,
            'total_exams': total_exams,
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'avg_score': round(avg_score, 2),
            'pass_rate': round(pass_rate, 2),
            'recent_exams': recent_exams,
            'recent_sessions': recent_sessions,
        }
        return render(request, 'admin/admin_stats.html', context)
    
    def user_management(self, request):
        """Halaman Manajemen User"""
        users = CustomUser.objects.all()
        context = {'users': users}
        return render(request, 'admin/user_management.html', context)


# Create custom admin site instance
admin_site = CustomAdminSite(name='custom_admin')


# =========================
# CUSTOM USER ADMIN
# =========================
@admin.register(CustomUser, site=admin_site)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_verified', 'is_active', 'date_joined', 'action_buttons')
    list_filter = ('user_type', 'is_verified', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('last_login', 'date_joined')
    actions = ['delete_selected']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'profile_picture')}),
        ('Permissions', {'fields': ('user_type', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    def action_buttons(self, obj):
        return format_html(
            '<a href="/admin/exam/customuser/{}/change/" class="button">Edit</a> '
            '<a href="/admin/exam/customuser/{}/delete/" class="button" style="color:red;">Delete</a>',
            obj.id, obj.id
        )
    action_buttons.short_description = 'Actions'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(is_superuser=False)

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)


# =========================
# INLINE MODEL (Choice)
# =========================
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    classes = ('collapse',)


# =========================
# DEPARTMENT ADMIN
# =========================
@admin.register(Department, site=admin_site)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'head_of_department', 'student_count', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code')
    raw_id_fields = ('head_of_department',)
    actions = ['delete_selected']

    def student_count(self, obj):
        return obj.members.filter(user_type='student').count()
    student_count.short_description = 'Students'


# =========================
# SUBJECT ADMIN
# =========================
@admin.register(Subject, site=admin_site)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'exam_count', 'credits', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('name', 'code')
    actions = ['delete_selected']

    def exam_count(self, obj):
        return obj.exam_subjects.count()
    exam_count.short_description = 'Exams'


# =========================
# EXAM ADMIN
# =========================
@admin.register(Exam, site=admin_site)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'exam_type', 'subject', 'status', 'start_time', 'end_time', 'session_count', 'is_active')
    list_filter = ('exam_type', 'status', 'is_active', 'start_time')
    search_fields = ('title', 'description')
    readonly_fields = ('exam_id', 'created_at', 'updated_at')
    filter_horizontal = ('allowed_departments', 'allowed_users')
    actions = ['delete_selected']

    fieldsets = (
        ('Basic Information', {'fields': ('exam_id', 'title', 'description', 'exam_type', 'status')}),
        ('Timing', {'fields': ('start_time', 'end_time', 'duration_minutes', 'result_publish_time')}),
        ('Settings', {'fields': ('passing_score', 'max_attempts', 'shuffle_questions', 'shuffle_choices')}),
        ('Security', {'fields': ('show_result_immediately', 'allow_back_navigation', 'require_webcam', 'require_microphone', 'enable_proctoring')}),
        ('Relations', {'fields': ('subject', 'created_by', 'allowed_departments', 'allowed_users')}),
        ('Metadata', {'fields': ('is_active', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def session_count(self, obj):
        return obj.examsession_set.count()
    session_count.short_description = 'Sessions'


# =========================
# QUESTION ADMIN
# =========================
@admin.register(Question, site=admin_site)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'question_type', 'exam', 'points', 'difficulty', 'is_active')
    list_filter = ('question_type', 'difficulty', 'is_active')
    search_fields = ('text',)
    readonly_fields = ('question_id', 'created_at', 'updated_at')
    inlines = [ChoiceInline]
    actions = ['delete_selected']

    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Question Text'


# =========================
# EXAM SESSION ADMIN
# =========================
@admin.register(ExamSession, site=admin_site)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'exam', 'status', 'score', 'start_time', 'time_spent_display', 'is_passed')
    list_filter = ('status', 'exam', 'start_time')
    search_fields = ('user__username', 'exam__title')
    readonly_fields = ('session_id', 'start_time', 'end_time', 'submitted_at')
    actions = ['delete_selected']

    def time_spent_display(self, obj):
        if obj.time_spent:
            minutes = obj.time_spent // 60
            seconds = obj.time_spent % 60
            return f"{minutes}m {seconds}s"
        return "N/A"
    time_spent_display.short_description = 'Time Spent'
    
    def is_passed(self, obj):
        if obj.score is not None:
            return obj.score >= obj.exam.passing_score
        return None
    is_passed.boolean = True
    is_passed.short_description = 'Passed'


# =========================
# FILTER UNTUK QUESTIONBANK
# =========================
class DifficultyFilter(SimpleListFilter):
    title = 'Question Difficulty'
    parameter_name = 'difficulty'

    def lookups(self, request, model_admin):
        return QuestionBank.DIFFICULTY_LEVELS

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(questions__difficulty=self.value())
        return queryset


# =========================
# QUESTION BANK ADMIN
# =========================
@admin.register(QuestionBank, site=admin_site)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'created_by', 'question_count', 'is_shared')
    list_filter = ('subject', 'created_by', DifficultyFilter)
    search_fields = ('name', 'description')

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'


# =========================
# OTHER MODELS
# =========================
admin_site.register(UserAnswer)
admin_site.register(ProctoringEvent)
admin_site.register(Certificate)
admin_site.register(SystemLog)
