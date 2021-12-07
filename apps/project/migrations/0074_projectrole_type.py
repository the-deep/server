# Generated by Django 3.2.9 on 2021-12-03 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0073_alter_projectjoinrequest_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectrole',
            name='type',
            field=models.CharField(choices=[
                ('project_owner', 'Project Owner'),
                ('admin', 'Admin'),
                ('member', 'Member'),
                ('reader', 'Reader'),
                ('reader_non_confidential', 'Reader (Non-confidential)'),
                ('unknown', 'Unknown'),
            ], default='unknown', max_length=50),
        ),
    ]
