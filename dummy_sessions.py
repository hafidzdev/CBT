from django.utils import timezone
from exam.models import Exam, CustomUser, Department, Subject, Question, Choice
import random, uuid

def run():
    teachers = CustomUser.objects.filter(user_type="teacher")
    if not teachers.exists():
        print("❌ Tidak ada teacher ditemukan.")
        return

    departments = list(Department.objects.all())
    if not departments:
        print("❌ Tidak ada department.")
        return

    subjects = list(Subject.objects.all())
    if not subjects:
        print("❌ Tidak ada subject.")
        return

    exam_types = ["quiz", "midterm", "final", "practice"]
    print(f"🧑‍🏫 Teachers: {teachers.count()} | 📚 Subjects: {len(subjects)}")

    for i in range(5):
        teacher = random.choice(teachers)
        subject = random.choice(subjects)
        dept = random.choice(departments)

        exam = Exam.objects.create(
            exam_id=uuid.uuid4(),
            title=f"Dummy Exam {i+1}",
            description="This is a generated dummy exam for testing visualization.",
            exam_type=random.choice(exam_types),
            status="published",
            duration_minutes=random.choice([30, 45, 60]),
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=2),
            result_publish_time=timezone.now() + timezone.timedelta(hours=3),
            max_score=100,
            passing_score=random.randint(50, 70),
            created_by=teacher,
            subject=subject,
            is_active=True,
        )

        # tambahkan relasi ke department & users
        exam.allowed_departments.add(dept)
        exam.save()

        # buat 5 soal
        for q in range(5):
            question = Question.objects.create(
                exam=exam,
                question_type="MC",
                text=f"Question {q+1} for {exam.title}",
                explanation="Auto-generated question",
                points=20,
                created_by=teacher,
            )

            # buat 4 pilihan jawaban
            correct_choice = random.randint(1, 4)
            for c in range(1, 5):
                Choice.objects.create(
                    question=question,
                    text=f"Option {c} for Q{q+1}",
                    is_correct=(c == correct_choice),
                    order=c
                )

        print(f"✅ Created exam: {exam.title} ({exam.exam_type}) by {teacher.username}")

    print("\n🎯 DONE: 5 dummy exams (each 5 questions) successfully created.")
