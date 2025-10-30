
from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0006_add_token_fields'), 
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='access_token',
            field=models.CharField(
                max_length=6,
                blank=True,
                null=True,
                unique=True,
                help_text='6-digit exam access token'
            ),
        ),
        migrations.AddField(
            model_name='exam',
            name='token_expiry',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Token expiry time (optional)'
            ),
        ),
        migrations.AddIndex(
            model_name='exam',
            index=models.Index(fields=['access_token'], name='exam_access_token_idx'),
        ),
    ]
