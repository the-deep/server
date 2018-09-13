# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-13 10:50
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_group', '0012_auto_20180604_0732'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0028_project_client_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectUserGroupMembership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='added_project_usergroups', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_usergroups', to='project.Project')),
                ('usergroup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usergroup_projects', to='user_group.UserGroup')),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='user_group_new',
            field=models.ManyToManyField(blank=True, related_name='project_usergroup_new', through='project.ProjectUserGroupMembership', to='user_group.UserGroup'),
        ),
    ]
