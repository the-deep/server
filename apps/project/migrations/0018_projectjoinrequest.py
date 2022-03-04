# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-06-04 07:06
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0017_auto_20180410_0405'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectJoinRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending', max_length=48)),
                ('responded_at', models.DateTimeField(blank=True, default=None, null=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.Project')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_join_requests', to=settings.AUTH_USER_MODEL)),
                ('responded_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='project_join_responses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-requested_at',),
            },
        ),
    ]