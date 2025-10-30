from django.core.management.base import BaseCommand
from exam.models import CustomUser

class Command(BaseCommand):
    help = 'Create super admin user for CBT System'

    def handle(self, *args, **options):
        if not CustomUser.objects.filter(username='superadmin').exists():
            user = CustomUser.objects.create_superuser(
                username='superadmin',
                email='superadmin@cbtsystem.com',
                password='SuperAdmin123!',
                user_type='superadmin',
                is_verified=True
            )
            self.stdout.write(
                self.style.SUCCESS('Successfully created super admin user')
            )
            self.stdout.write(
                self.style.SUCCESS('Username: superadmin')
            )
            self.stdout.write(
                self.style.SUCCESS('Password: SuperAdmin123!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Super admin user already exists')
            )