from django.core.management.base import BaseCommand
from django.utils import timezone
from exam.models import ExamToken

class Command(BaseCommand):
    help = 'Automatically rotate expired tokens'
    
    def handle(self, *args, **options):
        expired_tokens = ExamToken.objects.filter(
            status='active',
            expires_at__lte=timezone.now()
        )
        
        count = expired_tokens.count()
        expired_tokens.update(status='expired')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully rotated {count} expired tokens')
        )