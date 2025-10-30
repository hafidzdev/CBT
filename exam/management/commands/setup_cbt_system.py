from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from exam.models import Department, Subject, CustomUser

class Command(BaseCommand):
    help = 'Setup complete CBT System with sample data'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Create Super Admin
        if not User.objects.filter(username='superadmin').exists():
            superadmin = User.objects.create_superuser(
                username='superadmin',
                email='superadmin@cbtsystem.com',
                password='SuperAdmin123!',
                user_type='superadmin',
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS('✅ Super Admin created'))
        
        # Create Departments
        departments_data = [
            {'name': 'Computer Science', 'code': 'CS'},
            {'name': 'Mathematics', 'code': 'MATH'},
            {'name': 'Physics', 'code': 'PHY'},
        ]
        
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults=dept_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Department {dept.name} created'))
        
        # Create Subjects
        subjects_data = [
            {'name': 'Programming Fundamentals', 'code': 'CS101', 'department': 'CS', 'credits': 4},
            {'name': 'Database Systems', 'code': 'CS201', 'department': 'CS', 'credits': 3},
            {'name': 'Calculus I', 'code': 'MATH101', 'department': 'MATH', 'credits': 4},
            {'name': 'Classical Mechanics', 'code': 'PHY101', 'department': 'PHY', 'credits': 4},
        ]
        
        for subject_data in subjects_data:
            dept = Department.objects.get(code=subject_data['department'])
            subject, created = Subject.objects.get_or_create(
                code=subject_data['code'],
                defaults={
                    'name': subject_data['name'],
                    'department': dept,
                    'credits': subject_data['credits']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Subject {subject.name} created'))
        
        self.stdout.write(self.style.SUCCESS('🎉 CBT System setup completed successfully!'))
        self.stdout.write(self.style.SUCCESS('📝 Default login:'))
        self.stdout.write(self.style.SUCCESS('   Username: superadmin'))
        self.stdout.write(self.style.SUCCESS('   Password: SuperAdmin123!'))