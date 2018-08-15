# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-15 10:14
from __future__ import unicode_literals

from django.db import migrations


def create_roles_for_existing_users_in_usergroup(apps, schema_editor):
    ProjectMembership = apps.get_model('project', 'ProjectMembership')
    UserGroup = apps.get_model('user_group', 'UserGroup')
    ProjectRole = apps.get_model('project', 'ProjectRole')

    default_role = ProjectRole.objects.filter(is_default_role=True).first()

    for ug in UserGroup.objects.all():
        for member in ug.members.all():
            for project in ug.projects.all():
                ProjectMembership.objects.create(
                    member=member,
                    project=project,
                    role=default_role
                )



class Migration(migrations.Migration):

    dependencies = [
        ('project', '0034_auto_20180815_1013'),
    ]

    operations = [
        migrations.RunPython(create_roles_for_existing_users_in_usergroup),
    ]
