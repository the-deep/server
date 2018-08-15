# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-15 07:43
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0028_project_client_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('title', models.CharField(max_length=255, unique=True)),
                ('lead_permissions', models.IntegerField(default=0)),
                ('excerpt_permissions', models.IntegerField(default=0)),
                ('setup_permissions', models.IntegerField(default=0)),
                ('export_permissions', models.IntegerField(default=0)),
                ('is_creator_role', models.BooleanField(default=False)),
                ('is_default_role', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projectrole_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projectrole_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
    ]
