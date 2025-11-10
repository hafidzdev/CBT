from django.utils import timezone
from exam.models import (
    CustomUser, Department, Subject, QuestionBank, Question, Choice,
    Exam, ExamSession, Certificate, ProctoringEvent
)
import uuid

print("🚀 Memulai proses seeding data dummy...\n")

# ===================== 1. USERS =====================
admin, _ = CustomUser.objects.get_or_create(
    username="admin",
    defaults=dict(email="admin@example.com", user_type="admin", is_active=True, is_verified=True)
)
teacher, _ = CustomUser.objects.get_or_create(
    username="teacher1",
    defaults=dict(email="teacher1@example.com", user_type="teacher", is_active=True, is_verified=True)
)

students = []
for i in range(1, 6):
    s, _ = CustomUser.objects.get_or_create(
        username=f"student{i}",
        defaults=dict(email=f"student{i}@example.com", user_type="student", is_active=True, is_verified=True)
    )
    students.append(s)

print("✅ Users berhasil dibuat.")

# ===================== 2. DEPARTMENT & SUBJECT =====================
dep, _ = Department.objects.get_or_create(name="Teknik Informatika", code="TI")

subjects = []
subject_names = ["Algoritma", "Basis Data", "Pemrograman Web", "Jaringan Komputer", "Kecerdasan Buatan"]
for name in subject_names:
    subj, _ = Subject.objects.get_or_create(
        name=name,
        defaults=dict(code=name[:3].upper(), department=dep, credits=3, is_active=True)
    )
    subjects.append(subj)

print("✅ Department dan Subjects berhasil dibuat.")

# ===================== 3. QUESTION BANKS =====================
banks = []
for subj in subjects:
    bank, _ = QuestionBank.objects.get_or_create(
        name=f"Bank Soal {subj.name}",
        defaults=dict(
            description=f"Kumpulan soal-soal {subj.name} untuk latihan dan ujian.",
            subject=subj,
            created_by=teacher,
            is_shared=True,
            difficulty="medium"
        )
    )
    banks.append(bank)

print("✅ Question Banks berhasil dibuat.")

# ===================== 4. QUESTIONS & CHOICES =====================
for bank in banks:
    q1 = Question.objects.create(
        question_type='MC',
        text=f"Apa pengertian dasar dari {bank.subject.name}?",
        explanation="Soal ini untuk menguji pemahaman konsep dasar.",
        points=1,
        difficulty='easy',
        question_bank=bank,
        created_by=teacher,
    )
    Choice.objects.bulk_create([
        Choice(question=q1, text="Konsep dasar dan prinsip utama", is_correct=True),
        Choice(question=q1, text="Hanya kode program", is_correct=False),
        Choice(question=q1, text="Teori acak", is_correct=False),
        Choice(question=q1, text="Jawaban tidak ada", is_correct=False),
    ])

    q2 = Question.objects.create(
        question_type='TF',
        text=f"Apakah {bank.subject.name} berhubungan dengan pemrograman komputer?",
        explanation="Benar, semua topik ini bagian dari bidang informatika.",
        points=1,
        difficulty='medium',
        question_bank=bank,
        created_by=teacher,
    )
    Choice.objects.bulk_create([
        Choice(question=q2, text="Benar", is_correct=True),
        Choice(question=q2, text="Salah", is_correct=False),
    ])

print("✅ Questions dan Choices berhasil dibuat.")

# ===================== 5. EXAMS =====================
exams = []
for i, subj in enumerate(subjects, start=1):
    exam, _ = Exam.objects.get_or_create(
        title=f"Ujian Tengah Semester {subj.name}",
        defaults=dict(
            description=f"Ujian Tengah Semester untuk mata kuliah {subj.name}.",
            duration_minutes=60,
            max_score=100,
            passing_score=70,
            created_by=teacher,
            is_active=True,
        )
    )
    exams.append(exam)

print("✅ Exams berhasil dibuat.")

# ===================== 6. EXAM SESSIONS =====================
for i, student in enumerate(students, start=1):
    exam = exams[i % len(exams)]
    ExamSession.objects.get_or_create(
        user=student,
        exam=exam,
        defaults=dict(
            status="selesai",
            score=60 + i * 5,
            start_time=timezone.now() - timezone.timedelta(minutes=90),
            end_time=timezone.now(),
            time_spent=5400,
        )
    )

print("✅ Exam Sessions berhasil dibuat.")

# ===================== 7. CERTIFICATES =====================
for session in ExamSession.objects.all():
    if session.score and session.score >= session.exam.passing_score:
        Certificate.objects.get_or_create(
            session=session,
            defaults=dict(
                certificate_id=uuid.uuid4(),
                issued_at=timezone.now(),
                is_valid=True,
            )
        )

print("✅ Certificates berhasil dibuat.")

# ===================== 8. PROCTORING EVENTS =====================
for session in ExamSession.objects.all():
    ProctoringEvent.objects.get_or_create(
    session=session,
    event_type='no_face',
    severity='medium',
    description='Wajah peserta tidak terdeteksi.'
)
print("✅ Proctoring Events berhasil dibuat.")
print("\n🎯 SEMUA DATA DUMMY BERHASIL DIBUAT DENGAN RELASI LENGKAP!")
