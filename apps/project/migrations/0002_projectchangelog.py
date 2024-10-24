# Generated by Django 3.2.12 on 2022-08-19 05:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0001_auto_20220708_1137'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectChangeLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('action', models.SmallIntegerField(choices=[(1, 'Project Create'), (2, 'Project Details'), (3, 'Organization'), (4, 'Region'), (5, 'Membership'), (6, 'Framework'), (7, 'Multiple fields')])),
                ('diff', models.JSONField(blank=True, null=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
