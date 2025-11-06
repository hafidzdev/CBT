from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Q,F
from datetime import timedelta
from django.db import models
from .models import Exam, ExamSession, Question, Choice, UserAnswer, QuestionBank, StudentAnswer
from django.http import HttpResponse
from django.utils.encoding import smart_str
from django.conf import settings
from django.db import transaction
from .forms import ExamForm, AdminUserForm, AdminCreateUserForm, AdminUserEditForm
from .decorators import student_required
from exam.decorators import teacher_required
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from functools import wraps
from django.views.decorators.cache import cache_control
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.contrib.sessions.models import Session
from .decorators import admin_required



import json
import csv
import io

# GET User Data
User = get_user_model()

# Import semua model yang diperlukan
from .models import (
    CustomUser, Department, Subject, Exam, Question, 
    Choice, QuestionBank, ExamSession, UserAnswer, SystemLog
)
def simple_teacher_dashboard(request):
    return render(request, 'exam/simple_teacher_dashboard.html')

# Import semua forms yang diperlukan
from .forms import (
    QuestionForm, ChoiceFormSet, BulkQuestionForm, QuestionBankForm
)


# ===== DECORATORS UNTUK USER TYPE =====
def student_required(function=None):
    """Decorator untuk memastikan user adalah student"""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.user_type == 'student',
        login_url='/login/'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):

        # user udah login, cuma kita cek tipe-nya
        if not request.user.is_authenticated:
            return redirect('exam:login')

        if request.user.user_type != 'teacher':
            messages.error(request, "Unauthorized Access. Teacher only.")
            return redirect('exam:login')

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(function=None):
    """Decorator untuk memastikan user adalah admin/superadmin"""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.user_type in ['admin', 'superadmin'],
        login_url='/login/'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


# ===== AUTHENTICATION & REDIRECT VIEWS =====
# exam/views.py
def login_redirect(request):
    """Redirect user berdasarkan tipe setelah login"""
    if request.user.is_authenticated:
        if request.user.user_type == 'student':
            return redirect('exam:student_dashboard')  # GUNAKAN NAMESPACE
        elif request.user.user_type == 'teacher':
            return redirect('exam:teacher_dashboard')  # GUNAKAN NAMESPACE
        elif request.user.user_type in ['admin', 'superadmin']:
            return redirect('exam:admin_dashboard')  # GUNAKAN NAMESPACE
    return redirect('exam:login')  # GUNAKAN NAMESPACE
#addquistion
def simple_add_question(request):
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        option_a = request.POST.get('option_a')
        option_b = request.POST.get('option_b')
        option_c = request.POST.get('option_c')
        option_d = request.POST.get('option_d')
        correct_answer = request.POST.get('correct_answer')

        Question.objects.create(
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
        )
        return redirect('exam:teacher_dashboard')

    return render(request, 'exam/simple_add_question.html')


@login_required(login_url='exam:login')
def student_dashboard(request):
    """
    Dashboard untuk student dengan statistik lengkap
    """
    print(f"User: {request.user.username}")
    print(f"Authenticated: {request.user.is_authenticated}")
    print(f"User type: {request.user.user_type}")

    # Kalau bukan student, arahkan ke dashboard sesuai tipe user
    if request.user.user_type != 'student':
        if request.user.user_type == 'teacher':
            messages.info(request, "Redirected to teacher dashboard.")
            return redirect('exam:teacher_dashboard')
        elif request.user.user_type in ['admin', 'superadmin']:
            messages.info(request, "Redirected to admin dashboard.")
            return redirect('exam:admin_dashboard')
        else:
            messages.error(request, "Access denied. Please login with student account.")
            return redirect('exam:login')

    now = timezone.now()
    user = request.user

    try:
        # ===== Statistik Ujian =====
        total_exams_taken = ExamSession.objects.filter(user=user, is_completed=True).count()
        passed_exams = ExamSession.objects.filter(user=user, is_completed=True, score__gte=F('exam__passing_score')).count()
        avg_result = ExamSession.objects.filter(user=user, is_completed=True, score__isnull=False).aggregate(avg_score=Avg('score'))
        average_score = avg_result['avg_score'] or 0
        success_rate = round((passed_exams / total_exams_taken) * 100, 2) if total_exams_taken > 0 else 0

        # ===== Aktivitas Terbaru =====
        recent_sessions = ExamSession.objects.filter(user=user).select_related('exam', 'exam__subject').order_by('-start_time')[:5]

        # ===== Ujian Tersedia =====
        available_exams = Exam.objects.filter(
            status='published', is_active=True,
            start_time__lte=now, end_time__gte=now
        ).filter(
            Q(allowed_departments__isnull=True) | Q(allowed_departments=user.department)
        ).filter(
            Q(allowed_users__isnull=True) | Q(allowed_users=user)
        ).exclude(
            examsession__user=user, examsession__is_completed=True
        ).distinct().select_related('subject')[:6]

        # ===== Context untuk template =====
        context = {
            'total_exams_taken': total_exams_taken,
            'passed_exams': passed_exams,
            'average_score': round(average_score, 2),
            'success_rate': success_rate,
            'recent_sessions': recent_sessions,
            'available_exams': available_exams,
            'current_date': now,
            'user_department': user.department.name if user.department else "No Department",
        }

        return render(request, 'exam/student_dashboard.html', context)

    except Exception as e:
        print(f"Error in student_dashboard: {str(e)}")
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return render(request, 'exam/student_dashboard.html', {})

@login_required
@student_required
def my_exams(request):
    """Halaman exams untuk student dengan sistem token"""
    if request.user.user_type != 'student':
        messages.error(request, "Access denied. Student area only.")
        return redirect('exam:login')
    
    now = timezone.now()
    user = request.user
    
    # Get available exams
    available_exams = Exam.objects.filter(
        status='published',
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    ).filter(
        Q(allowed_departments__isnull=True) | 
        Q(allowed_departments=user.department)
    ).filter(
        Q(allowed_users__isnull=True) | 
        Q(allowed_users=user)
    ).exclude(
        examsession__user=user,
        examsession__is_completed=True
    ).distinct().select_related('subject', 'created_by')
    
    # Get ongoing sessions
    ongoing_sessions = ExamSession.objects.filter(
        user=user,
        end_time__isnull=True,
        is_completed=False
    ).select_related('exam')
    
    # Get completed sessions
    completed_sessions = ExamSession.objects.filter(
        user=user,
        is_completed=True
    ).select_related('exam').order_by('-end_time')
    
    # Get upcoming exams
    upcoming_exams = Exam.objects.filter(
        status='published',
        is_active=True,
        start_time__gt=now
    ).filter(
        Q(allowed_departments__isnull=True) | 
        Q(allowed_departments=user.department)
    ).filter(
        Q(allowed_users__isnull=True) | 
        Q(allowed_users=user)
    ).distinct().select_related('subject').order_by('start_time')[:5]
    
    # Calculate statistics
    total_exams = available_exams.count() + ongoing_sessions.count() + completed_sessions.count()
    
    # Calculate average score
    avg_score = completed_sessions.aggregate(avg_score=Avg('score'))['avg_score'] or 0
    
    # Calculate success rate
    passed_exams = completed_sessions.filter(score__gte=F('exam__passing_score')).count()
    success_rate = round((passed_exams / completed_sessions.count() * 100), 2) if completed_sessions.count() > 0 else 0
    
    context = {
        'available_exams': available_exams,
        'ongoing_sessions': ongoing_sessions,
        'completed_sessions': completed_sessions,
        'upcoming_exams': upcoming_exams,
        'total_exams': total_exams,
        'average_score': round(avg_score, 2),
        'success_rate': success_rate,
        'current_date': now,
    }
    
    return render(request, 'exam/my_exams.html', context)

@login_required
@student_required
# views.py - perbaiki take_exam view
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, is_active=True)
    
    # Check if user is student
    if request.user.user_type != 'student':
        return redirect('exam_access_denied')
    
    # Check exam availability
    now = timezone.now()
    
    # Exam hasn't started yet
    if exam.start_time and now < exam.start_time:
        context = {
            'title': 'Exam Not Started',
            'message': f'This exam will start on {exam.start_time.strftime("%B %d, %Y at %H:%M")}.',
            'icon': 'fas fa-clock',
            'color': 'blue'
        }
        return render(request, 'exam/error_pages.html', context)
    
    # Exam has ended
    if exam.end_time and now > exam.end_time:
        context = {
            'title': 'Exam Ended',
            'message': f'This exam ended on {exam.end_time.strftime("%B %d, %Y at %H:%M")}.',
            'icon': 'fas fa-calendar-times',
            'color': 'red'
        }
        return render(request, 'exam/error_pages.html', context)
    
    # Check if exam is published
    if exam.status != 'published':
        context = {
            'title': 'Exam Not Available',
            'message': 'This exam is not currently available.',
            'icon': 'fas fa-ban',
            'color': 'yellow'
        }
        return render(request, 'exam/error_pages.html', context)
    
    # Check user permissions
    if (exam.allowed_departments.exists() and 
        not exam.allowed_departments.filter(id=request.user.department.id).exists()):
        context = {
            'title': 'Access Denied',
            'message': 'You do not have permission to take this exam.',
            'icon': 'fas fa-lock',
            'color': 'red'
        }
        return render(request, 'exam/error_pages.html', context)
    
    # Check max attempts
    completed_sessions = ExamSession.objects.filter(
        user=request.user,
        exam=exam,
        is_completed=True
    ).count()
    
    if completed_sessions >= exam.max_attempts:
        context = {
            'title': 'Maximum Attempts Reached',
            'message': f'You have already completed this exam {completed_sessions} time(s). Maximum attempts: {exam.max_attempts}.',
            'icon': 'fas fa-exclamation-triangle',
            'color': 'orange'
        }
        return render(request, 'exam/error_pages.html', context)
    
    # Check if user has ongoing session
    ongoing_session = ExamSession.objects.filter(
        user=request.user,
        exam=exam,
        end_time__isnull=True
    ).first()
    
    if not ongoing_session:
        ongoing_session = ExamSession.objects.create(
            user=request.user,
            exam=exam,
            start_time=timezone.now(),
            attempt_number=completed_sessions + 1
        )
    
    # Prepare questions data for JavaScript
    questions_data = []
    questions = exam.questions.all().prefetch_related('choices')
    
    # Apply shuffle if enabled
    if exam.shuffle_questions:
        questions = questions.order_by('?')
    
    for question in questions:
        choices = list(question.choices.all())
        
        # Apply shuffle to choices if enabled
        if exam.shuffle_choices:
            import random
            random.shuffle(choices)
        
        questions_data.append({
            'id': question.id,
            'text': question.text,
            'image': question.image.url if question.image else None,
            'options': [
                {
                    'id': choice.id,
                    'text': choice.text
                } for choice in choices
            ],
            'answered': False,
            'selected_option': None,
            'flagged': False
        })
    
    context = {
        'exam': exam,
        'questions_data': json.dumps(questions_data),
        'ongoing_session': ongoing_session,
        'shuffle_questions': exam.shuffle_questions,
        'shuffle_choices': exam.shuffle_choices,
        'allow_back_navigation': exam.allow_back_navigation,
    }
    
    return render(request, 'exam/take_exam.html', context)

@csrf_exempt
def submit_exam(request, exam_id):
    if request.method == 'POST':
        exam = get_object_or_404(Exam, id=exam_id)
        data = json.loads(request.body)
        
        # Get or create exam session
        session = ExamSession.objects.filter(
            user=request.user,
            exam=exam,
            end_time__isnull=True
        ).first()
        
        if session:
            session.end_time = timezone.now()
            session.time_spent = data.get('time_spent', 0)
            
            # Calculate score
            total_questions = exam.questions.count()
            correct_answers = 0
            
            for answer_data in data.get('answers', []):
                question = get_object_or_404(Question, id=answer_data['question_id'])
                selected_choice = get_object_or_404(Choice, id=answer_data['option_id'])
                
                # Create UserAnswer record
                user_answer = UserAnswer.objects.create(
                    session=session,
                    question=question,
                    is_correct=selected_choice.is_correct
                )
                user_answer.selected_choices.add(selected_choice)
                
                if selected_choice.is_correct:
                    correct_answers += 1
            
            # Update session statistics
            session.score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            session.total_questions = total_questions
            session.answered_questions = len(data.get('answers', []))
            session.correct_answers = correct_answers
            session.wrong_answers = session.answered_questions - correct_answers
            session.status = 'completed'
            session.is_completed = True
            session.save()
            
            return JsonResponse({'session_id': session.id, 'score': session.score})
        
        return JsonResponse({'error': 'Session not found'}, status=400)@login_required
# views.py - tambahkan fungsi exam_results
@student_required
def exam_results(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id, user=request.user)
    
    # Calculate statistics
    total_questions = session.total_questions
    correct_answers = session.correct_answers
    incorrect_answers = session.wrong_answers
    correct_percentage = round((correct_answers / total_questions) * 100) if total_questions > 0 else 0
    incorrect_percentage = 100 - correct_percentage
    
    # Calculate time taken
    if session.start_time and session.end_time:
        time_taken_minutes = (session.end_time - session.start_time).total_seconds() / 60
        time_taken = f"{int(time_taken_minutes)} min {int((time_taken_minutes % 1) * 60)} sec"
        time_efficiency = round((time_taken_minutes / session.exam.duration_minutes) * 100)
    else:
        time_taken = "N/A"
        time_efficiency = 0
    
    # Get user answers for review
    user_answers = session.user_answers.all().select_related('question')
    
    context = {
        'session': session,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
        'correct_percentage': correct_percentage,
        'incorrect_percentage': incorrect_percentage,
        'time_taken': time_taken,
        'time_efficiency': min(time_efficiency, 100),
        'user_answers': user_answers,
    }
    
    return render(request, 'exam/exam_results.html', context)

@login_required
def student_results(request):
    sessions = ExamSession.objects.filter(
        user=request.user,
        is_completed=True
    ).select_related('exam').order_by('-end_time')

    return render(request, 'exam/student_results.html', {'sessions': sessions})


@login_required
def student_result_detail(request, session_id):
    session = get_object_or_404(
        ExamSession,
        id=session_id,
        user=request.user
    )
    
    answers = StudentAnswer.objects.filter(session=session).select_related('question', 'selected_choice')
    
    for a in answers:
        a.correct_choice = a.question.choices.filter(is_correct=True).first()


    return render(request, 'exam/student_result_detail.html', {
        'session': session,
        'answers': answers
    })


# ===== TEACHER VIEWS =====
@login_required(login_url='exam:login')
@teacher_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def teacher_dashboard(request):

    if not request.user.is_authenticated:
        return redirect('exam:login')
    
    user = request.user
    
    # Total Exams dibuat guru ini
    total_exams = Exam.objects.filter(created_by=user).count()

    # Total Questions dibuat guru ini
    total_questions = QuestionBank.objects.filter(created_by=user).count()

    # Semua sesi ujian dari ujian yang dia buat
    total_sessions = ExamSession.objects.filter(exam__created_by=user).count()

    # List ujian miliknya
    my_exams = Exam.objects.filter(created_by=user).select_related('subject').order_by('-created_at')

    # Activity siswa terakhir (5 terbaru saja biar clean)
    recent_sessions = ExamSession.objects.filter(
        exam__created_by=user,
        is_completed=True
    ).select_related('user', 'exam').order_by('-end_time')[:5]

    context = {
        'total_exams': total_exams,
        'total_questions': total_questions,
        'total_sessions': total_sessions,
        'my_exams': my_exams,
        'recent_sessions': recent_sessions,
    }

    return render(request, 'exam/teacher_dashboard.html', context)


@login_required
@teacher_required
def teacher_questions(request):
    """Halaman utama management soal untuk teacher"""
    my_questions = Question.objects.filter(created_by=request.user).order_by('-created_at')
    my_question_banks = QuestionBank.objects.filter(created_by=request.user)
    my_exams = Exam.objects.filter(created_by=request.user)
    
    context = {
        'my_questions': my_questions,
        'my_question_banks': my_question_banks,
        'my_exams': my_exams,
    }
    return render(request, 'exam/teacher_questions.html', context)

@login_required
@teacher_required
def add_question(request):
    """Tambah soal single"""
    if request.method == 'POST':
        question_form = QuestionForm(request.POST, request.FILES, user=request.user)
        choice_formset = ChoiceFormSet(request.POST)
        
        if question_form.is_valid() and choice_formset.is_valid():
            question = question_form.save(commit=False)
            question.created_by = request.user
            question.save()
            
            # Save choices
            choices = choice_formset.save(commit=False)
            for choice in choices:
                choice.question = question
                choice.save()
            
            messages.success(request, 'Question added successfully!')
            return redirect('exam:teacher_questions')
    else:
        question_form = QuestionForm(user=request.user)
        choice_formset = ChoiceFormSet()
    
    context = {
        'question_form': question_form,
        'choice_formset': choice_formset,
        'title': 'Add New Question'
    }
    return render(request, 'exam/question_form.html', context)

@login_required
@teacher_required
def edit_question(request, question_id):
    """Edit soal yang sudah ada"""
    question = get_object_or_404(Question, id=question_id, created_by=request.user)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST, request.FILES, instance=question, user=request.user)
        choice_formset = ChoiceFormSet(request.POST, instance=question)
        
        if question_form.is_valid() and choice_formset.is_valid():
            question_form.save()
            choice_formset.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('exam:teacher_questions')
    else:
        question_form = QuestionForm(instance=question, user=request.user)
        choice_formset = ChoiceFormSet(instance=question)
    
    context = {
        'question_form': question_form,
        'choice_formset': choice_formset,
        'title': 'Edit Question'
    }
    return render(request, 'exam/question_form.html', context)

@login_required
@teacher_required
def delete_question(request, question_id):
    """Hapus soal"""
    question = get_object_or_404(Question, id=question_id, created_by=request.user)
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return redirect('exam:teacher_questions')
    
    return render(request, 'exam/confirm_delete.html', {'object': question})

@login_required
@teacher_required
def upload_questions_csv(request, question_bank_id=None):
    # Get available exams for the dropdown
    exams = Exam.objects.filter(created_by=request.user, is_active=True)
    
    if request.method == 'POST':
        try:
            csv_file = request.FILES.get('file')
            exam_id = request.POST.get('exam_id')  # ✅ GET exam_id FROM FORM
            question_bank_id = request.POST.get('question_bank_id')
            
            # Validasi: Pastikan file ada
            if not csv_file:
                messages.error(request, 'Please select a CSV file to upload.')
                return render(request, 'exam/bulk_upload.html', {'exams': exams})
            
            # Validasi: Pastikan file adalah CSV
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return render(request, 'exam/bulk_upload.html', {'exams': exams})
            
            # Validasi: Pastikan exam dipilih
            if not exam_id:
                messages.error(request, 'Please select an exam for these questions.')
                return render(request, 'exam/bulk_upload.html', {'exams': exams})
            
            # Baca file CSV
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            
            questions_created = 0
            with transaction.atomic():  # ✅ GUNAKAN TRANSACTION
                for row_num, row in enumerate(csv.reader(io_string, delimiter=','), 1):
                    # Skip header row
                    if row_num == 1:
                        continue
                    
                    # Skip empty rows
                    if not any(row) or len(row) < 5:
                        continue
                    
                    try:
                        # Process each row
                        question_text = row[0].strip()
                        question_type = row[1].strip().lower()
                        points = int(row[2]) if row[2].strip().isdigit() else 1
                        difficulty = row[3].strip().lower()
                        correct_answer = row[4].strip().upper()
                        
                        # Validasi difficulty
                        if difficulty not in ['easy', 'medium', 'hard']:
                            difficulty = 'medium'
                        
                        # Validasi question type
                        if question_type not in ['multiple_choice', 'true_false', 'short_answer', 'essay']:
                            question_type = 'multiple_choice'
                        
                        # Create question
                        question = Question.objects.create(
                            text=question_text,
                            question_type=question_type,
                            points=points,
                            difficulty=difficulty,
                            exam_id=exam_id,  # ✅ GUNAKAN exam_id YANG SUDAH DIPILIH
                            created_by=request.user
                        )
                        
                        # Jika ada question_bank_id, assign ke question bank
                        if question_bank_id:
                            question.question_bank_id = question_bank_id
                            question.save()
                        
                        # Create choices untuk multiple choice questions
                        if question_type == 'multiple_choice' and len(row) >= 9:
                            choices = row[5:9]  # Options A, B, C, D
                            for i, choice_text in enumerate(choices):
                                if choice_text.strip():  # Only create if choice text is not empty
                                    is_correct = (chr(65 + i) == correct_answer)  # A=0, B=1, etc.
                                    Choice.objects.create(
                                        question=question,
                                        text=choice_text.strip(),
                                        is_correct=is_correct
                                    )
                        
                        # Create choices untuk true_false questions
                        elif question_type == 'true_false':
                            # Create True choice
                            Choice.objects.create(
                                question=question,
                                text="True",
                                is_correct=(correct_answer.upper() == 'TRUE' or correct_answer == 'A')
                            )
                            # Create False choice  
                            Choice.objects.create(
                                question=question,
                                text="False", 
                                is_correct=(correct_answer.upper() == 'FALSE' or correct_answer == 'B')
                            )
                        
                        questions_created += 1
                        
                    except Exception as e:
                        # Skip row jika ada error dan continue ke row berikutnya
                        print(f"Error processing row {row_num}: {e}")
                        continue
            
            messages.success(request, f'Successfully uploaded {questions_created} questions!')
            return redirect('exam:teacher_questions')  # Sesuaikan dengan nama URL Anda
            
        except Exception as e:
            messages.error(request, f'Error uploading file: {str(e)}')
            return render(request, 'exam/bulk_upload.html', {'exams': exams})
    
    return render(request, 'exam/bulk_upload.html', {'exams': exams})

@login_required
@teacher_required
def create_question_bank(request):
    """Buat bank soal baru"""
    if request.method == 'POST':
        form = QuestionBankForm(request.POST)
        if form.is_valid():
            question_bank = form.save(commit=False)
            question_bank.created_by = request.user
            question_bank.save()
            messages.success(request, 'Question bank created successfully!')
            return redirect('exam:teacher_questions')
    else:
        form = QuestionBankForm()
    
    context = {
        'form': form,
        
    }
    return render(request, 'exam/question_bank_form.html', context)

@login_required
@teacher_required
def question_bank_detail(request, bank_id):
    """Detail bank soal"""
    question_bank = get_object_or_404(QuestionBank, id=bank_id, created_by=request.user)
    questions = question_bank.questions.all()
    
    context = {
        'question_bank': question_bank,
        'questions': questions,
    }
    return render(request, 'exam/question_bank_detail.html', context)

# ===== ADMIN VIEWS =====
# exam/views.py
@login_required
@admin_required
def admin_dashboard(request):
    """Dashboard untuk admin"""
    # Check if user is admin
    if request.user.user_type not in ['admin', 'superadmin']:
        messages.error(request, "Access denied. Admin access required.")
        return redirect('exam:login')
    
    # System statistics
    total_users = CustomUser.objects.count()
    total_students = CustomUser.objects.filter(user_type='student').count()
    total_teachers = CustomUser.objects.filter(user_type='teacher').count()
    total_exams = Exam.objects.count()
    total_sessions = ExamSession.objects.count()
    active_sessions = ExamSession.objects.filter(status='in_progress').count()
    
    # Recent exams
    recent_exams = Exam.objects.select_related('subject', 'created_by').order_by('-created_at')[:5]
    
    # System logs
    system_logs = SystemLog.objects.select_related('user').order_by('-created_at')[:10]
    
    # Today's activity
    today = timezone.now().date()
    today_exams = Exam.objects.filter(created_at__date=today).count()
    today_sessions = ExamSession.objects.filter(start_time__date=today).count()
    
    # Performance metrics
    avg_score = ExamSession.objects.filter(score__isnull=False).aggregate(Avg('score'))['score__avg'] or 0
    completed_sessions = ExamSession.objects.filter(is_completed=True)
    pass_rate = (completed_sessions.filter(score__gte=60).count() / completed_sessions.count() * 100) if completed_sessions.count() > 0 else 0

    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_exams': total_exams,
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'today_exams': today_exams,
        'today_sessions': today_sessions,
        'avg_score': round(avg_score, 2),
        'pass_rate': round(pass_rate, 2),
        'recent_exams': recent_exams,
        'system_logs': system_logs,
    }
    
    return render(request, 'exam/admin_dashboard.html', context)

@login_required
@admin_required
def admin_stats(request):
    """Statistics page untuk admin"""
    # Basic statistics
    total_users = CustomUser.objects.count()
    total_exams = Exam.objects.count()
    total_sessions = ExamSession.objects.count()
    active_sessions = ExamSession.objects.filter(status='in_progress').count()
    
    # Performance metrics
    avg_score = ExamSession.objects.filter(score__isnull=False).aggregate(Avg('score'))['score__avg'] or 0
    pass_rate = (ExamSession.objects.filter(score__gte=60).count() / total_sessions * 100) if total_sessions > 0 else 0
    
    # Recent activity
    recent_exams = Exam.objects.order_by('-created_at')[:5]
    recent_sessions = ExamSession.objects.select_related('user', 'exam').order_by('-start_time')[:10]
    
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

# USER Management

@login_required
@admin_required
def user_management_list(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'admin/user_management.html', {'users': users})


@login_required
@admin_required
def admin_user_create(request):
    if request.method == "POST":
        form = AdminCreateUserForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ User berhasil dibuat.")
            return redirect('exam:admin_user_list')
    else:
        form = AdminCreateUserForm()
    return render(request, 'admin/admin_user_create.html', {'form': form})

@login_required
@admin_required
def admin_user_detail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    # Ambil riwayat ujian user ini
    exam_history = ExamSession.objects.filter(
        user=user,
        is_completed=True
    ).select_related('exam').order_by('-end_time')

    # Data untuk chart
    chart_labels = [s.exam.title for s in exam_history[::-1]]  # urut paling lama ke terbaru
    chart_scores = [s.score for s in exam_history[::-1]]

    context = {
        'user': user,
        'exam_history': exam_history,
        'chart_labels': chart_labels,
        'chart_scores': chart_scores,
    }
    return render(request, 'admin/admin_user_detail.html', context)


@login_required
@admin_required
def admin_user_edit(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == "POST":
        form = AdminUserEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ User updated successfully.")
            return redirect("exam:admin_user_view", user_id=user.id)
    else:
        form = AdminUserEditForm(instance=user)

    return render(request, "admin/admin_user_form.html", {"form": form, "user": user})



@login_required
@admin_required
def user_management_toggle(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, "User status updated.")
    return redirect('exam:admin_user_list')


@login_required
@admin_required
def user_management_delete(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, "User deleted.")
    return redirect('exam:admin_user_list')


# ====================================

@login_required
@admin_required
def user_management(request):
    """User management page untuk admin"""
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Filter functionality
    user_type_filter = request.GET.get('user_type')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    context = {
        'users': users,
    }
    return render(request, 'admin/user_management.html', context)

# ===== FALLBACK VIEWS (jika decorator masih error) =====
def teacher_dashboard_fallback(request):
    """Fallback view untuk teacher dashboard tanpa decorator"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied. Teacher access required.')
        return redirect('login')
    
    # Panggil fungsi teacher_dashboard asli
    return teacher_dashboard(request)

def add_question_fallback(request):
    """Fallback view untuk add question tanpa decorator"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied. Teacher access required.')
        return redirect('login')
    
    # Panggil fungsi add_question asli
    return add_question(request)

def download_question_bank_template(request):
    """
    View untuk mendownload template CSV Question Bank
    """
    # Create HttpResponse dengan content type CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="question_bank_template.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Header untuk template CSV
    headers = [
        'Question Text',
        'Question Type (multiple_choice/true_false/short_answer/essay)',
        'Option A',
        'Option B', 
        'Option C',
        'Option D',
        'Correct Answer (A/B/C/D or text for short answers)',
        'Points',
        'Difficulty (easy/medium/hard)',
        'Explanation (optional)'
    ]
    
    # Write headers
    writer.writerow([smart_str(header) for header in headers])
    
    # Write example rows
    examples = [
        [
            'Apa ibu kota Indonesia?',
            'multiple_choice',
            'Jakarta',
            'Surabaya',
            'Bandung',
            'Medan',
            'A',
            '10',
            'easy',
            'Jakarta adalah ibu kota Indonesia sejak 1945'
        ],
        [
            'Python adalah bahasa pemrograman compiled',
            'true_false',
            'True',
            'False',
            '',
            '',
            'B',
            '5',
            'easy',
            'Python adalah interpreted language'
        ]
    ]
    
    for example in examples:
        writer.writerow([smart_str(field) for field in example])
    
    return response

# =========================
@login_required
@teacher_required
def download_question_bank_template(request):
    """Download CSV template for questions"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="question_template.csv"'
    
    writer = csv.writer(response)
    # Write header
    writer.writerow([
        'Question Text', 'Question Type', 'Points', 'Difficulty', 
        'Correct Answer', 'Option A', 'Option B', 'Option C', 'Option D'
    ])
    # Write example rows
    writer.writerow([
        'What is 2+2?', 'multiple_choice', '5', 'easy', 'A', 
        '4', '5', '6', '7'
    ])
    writer.writerow([
        'Python is interpreted language', 'true_false', '3', 'easy', 'A',
        'True', 'False', '', ''
    ])
    
    return response

@login_required
@teacher_required

def auto_wrap_math(text):
    """Otomatis bungkus teks yang mengandung rumus dengan $...$ biar MathJax render."""
    if not text:
        return text

    # Kalau sudah mengandung $ berarti user sengaja → biarin
    if "$" in text:
        return text

    # Deteksi "tanda khas rumus"
    math_indicators = ["^", "_", "√", "∫", "Σ", "π", "=", "+", "-", "/", "*"]
    if any(sym in text for sym in math_indicators):
        return f"${text}$"

    return text


def bulk_upload_questions(request):
    exams = Exam.objects.filter(created_by=request.user, is_active=True)
    question_banks = QuestionBank.objects.filter(created_by=request.user)
    
    if request.method == 'POST':
        try:
            csv_file = request.FILES.get('file')
            exam_id = request.POST.get('exam_id')
            question_bank_id = request.POST.get('question_bank_id')
            
            if not csv_file:
                messages.error(request, 'Please select a CSV file to upload.')
                return render(request, 'exam/bulk_upload.html', {'exams': exams, 'question_banks': question_banks})
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file (.csv).')
                return render(request, 'exam/bulk_upload.html', {'exams': exams, 'question_banks': question_banks})

            if not exam_id:
                messages.error(request, 'Please select an exam.')
                return render(request, 'exam/bulk_upload.html', {'exams': exams, 'question_banks': question_banks})
            
            # ✅ UTF-8 BOM Safe (biar ARAB / PEGON masuk utuh)
            data_set = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(data_set)
            
            questions_created = 0
            
            with transaction.atomic():
                for row_num, row in enumerate(csv.reader(io_string, delimiter=','), 1):
                    if row_num == 1 or not any(row) or len(row) < 5:
                        continue

                    try:
                        # ✅ Jangan strip teks → biarkan RTL natural
                        question_text = row[0]
                        question_type = row[1].strip().lower()
                        points = int(row[2]) if row[2].strip().isdigit() else 1
                        difficulty = row[3].strip().lower()
                        correct_answer = row[4].strip().upper()

                        if difficulty not in ['easy', 'medium', 'hard']:
                            difficulty = 'medium'

                        if question_type not in ['multiple_choice', 'true_false', 'short_answer', 'essay']:
                            question_type = 'multiple_choice'

                        question = Question.objects.create(
                            text=question_text,
                            question_type=question_type,
                            points=points,
                            difficulty=difficulty,
                            exam_id=exam_id,
                            created_by=request.user
                        )

                        if question_bank_id:
                            question.question_bank_id = question_bank_id
                            question.save()

                        # ✅ MULTIPLE CHOICE (pilihan tidak di-strip)
                        if question_type == 'multiple_choice' and len(row) >= 9:
                            choices = row[5:9]
                            for i, choice in enumerate(choices):
                                if choice:
                                    Choice.objects.create(
                                        question=question,
                                        text=choice,
                                        is_correct=(chr(65 + i) == correct_answer)
                                    )

                        # ✅ TRUE / FALSE clean
                        elif question_type == 'true_false':
                            Choice.objects.create(question=question, text="True", is_correct=(correct_answer in ['TRUE', 'A']))
                            Choice.objects.create(question=question, text="False", is_correct=(correct_answer in ['FALSE', 'B']))

                        questions_created += 1
                    
                    except Exception as e:
                        print(f"Row {row_num} skipped: {e}")
                        continue

            messages.success(request, f'Successfully uploaded {questions_created} questions (Arabic/Pegon supported).')
            return redirect('exam:teacher_questions')

        except Exception as e:
            messages.error(request, f'Error uploading file: {str(e)}')
    
    return render(request, 'exam/bulk_upload.html', {'exams': exams, 'question_banks': question_banks})

    
@login_required
@teacher_required
def create_exam(request):
    """Form untuk membuat exam baru"""
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            messages.success(request, 'Exam created successfully!')
            return redirect('exam:teacher_dashboard')  # arahkan ke dashboard guru
    else:
        form = ExamForm()

    context = {
        'title': 'Create Exam',
        'form': form
    }
    return render(request, 'exam/create_exam_form.html', context)

@never_cache
@login_required
def custom_logout(request):

    logout(request)
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('exam:login')

@login_required
@student_required
# views.py - tambahkan view untuk error pages
def exam_not_available(request):
    return render(request, 'exam/error_pages.html', {
        'title': 'Exam Not Available',
        'message': 'This exam is not available at the moment.',
        'icon': 'fas fa-clock',
        'color': 'yellow'
    })

def exam_ended(request):
    return render(request, 'exam/error_pages.html', {
        'title': 'Exam Ended',
        'message': 'This exam has already ended.',
        'icon': 'fas fa-calendar-times',
        'color': 'red'
    })

def exam_access_denied(request):
    return render(request, 'exam/error_pages.html', {
        'title': 'Access Denied',
        'message': 'You do not have permission to access this exam.',
        'icon': 'fas fa-ban',
        'color': 'red'
    })

def exam_token_access(request):
    """
    View untuk halaman token akses ujian
    """
    if not request.user.is_authenticated:
        return redirect('exam:login')
    
    if request.user.user_type != 'student':
        messages.error(request, "Access denied. Student area only.")
        return redirect('exam:login')
    
    now = timezone.now()
    
    # Get available exams
    available_exams = Exam.objects.filter(
        status='published',
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    ).filter(
        Q(allowed_departments__isnull=True) | 
        Q(allowed_departments=request.user.department)
    ).filter(
        Q(allowed_users__isnull=True) | 
        Q(allowed_users=request.user)
    ).exclude(
        examsession__user=request.user,
        examsession__is_completed=True
    ).distinct().select_related('subject')
    
    context = {
        'available_exams': available_exams,
        'current_time': now,
    }
    
    return render(request, 'exam/exam_token.html', context)

# exam/views.py - tambahkan view untuk validasi token
@login_required
@student_required
def validate_exam_token(request):
    """View untuk validasi token dan akses ujian"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token', '').strip().upper()
            
            if len(token) != 6:
                return JsonResponse({
                    'valid': False,
                    'message': 'Token must be 6 characters long'
                })
            
            # Cari exam dengan token yang valid
            exam = Exam.objects.filter(
                access_token=token,
                is_active=True,
                status='published'
            ).first()
            
            if not exam:
                return JsonResponse({
                    'valid': False,
                    'message': 'Invalid token or exam not found'
                })
            
            # Cek expiry token
            if not exam.is_token_valid():
                return JsonResponse({
                    'valid': False,
                    'message': 'Token has expired'
                })
            
            # Cek waktu ujian
            now = timezone.now()
            if now < exam.start_time:
                return JsonResponse({
                    'valid': False,
                    'message': f'Exam starts at {exam.start_time.strftime("%Y-%m-%d %H:%M")}'
                })
            
            if now > exam.end_time:
                return JsonResponse({
                    'valid': False,
                    'message': 'Exam has ended'
                })
            
            # Cek permission user
            if (exam.allowed_departments.exists() and 
                not exam.allowed_departments.filter(id=request.user.department.id).exists()):
                return JsonResponse({
                    'valid': False,
                    'message': 'You are not allowed to access this exam'
                })
            
            # Cek max attempts
            completed_attempts = ExamSession.objects.filter(
                user=request.user,
                exam=exam,
                is_completed=True
            ).count()
            
            if completed_attempts >= exam.max_attempts:
                return JsonResponse({
                    'valid': False,
                    'message': f'Maximum attempts ({exam.max_attempts}) reached for this exam'
                })
            
            return JsonResponse({
                'valid': True,
                'exam_id': exam.id,
                'exam_title': exam.title,
                'message': 'Token validated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'message': f'Validation error: {str(e)}'
            })
    
    return JsonResponse({'valid': False, 'message': 'Invalid request method'})



@login_required
@student_required
def access_exam_with_token(request, token):
    """Akses ujian langsung dengan token"""
    token = token.upper()
    
    try:
        exam = get_object_or_404(
            Exam, 
            access_token=token,
            is_active=True,
            status='published'
        )
        
        # Validasi yang sama seperti di atas
        if not exam.is_token_valid():
            messages.error(request, 'Token has expired')
            return redirect('exam:my_exams')
        
        now = timezone.now()
        if now < exam.start_time:
            messages.error(request, f'Exam starts at {exam.start_time.strftime("%Y-%m-%d %H:%M")}')
            return redirect('exam:my_exams')
        
        if now > exam.end_time:
            messages.error(request, 'Exam has ended')
            return redirect('exam:my_exams')
        
        # Redirect ke halaman take exam
        return redirect('exam:take_exam', exam_id=exam.id)
        
    except Exam.DoesNotExist:
        messages.error(request, 'Invalid exam token')
        return redirect('exam:my_exams')