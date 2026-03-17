from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_resume_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='resume',
            name='uploaded_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
