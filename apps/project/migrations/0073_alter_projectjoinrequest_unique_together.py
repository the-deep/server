# Generated by Django 3.2.5 on 2021-09-07 04:42

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0072_merge_20210805_0715'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='projectjoinrequest',
            unique_together={('project', 'requested_by')},
        ),
    ]