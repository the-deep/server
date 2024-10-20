# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-15 08:25
from __future__ import unicode_literals

from django.db import migrations


def update_current_role_values(apps, schema_editor):
    ProjectMembership = apps.get_model('project', 'ProjectMembership')
    ProjectJoinRequest= apps.get_model('project', 'ProjectJoinRequest')
    ProjectRole = apps.get_model('project', 'ProjectRole')

    creator_role = ProjectRole.objects.filter(is_creator_role=True).first()
    default_role = ProjectRole.objects.filter(is_default_role=True).first()

    ProjectMembership.objects.filter(role='admin').update(newrole=creator_role.id)
    ProjectMembership.objects.filter(role='normal').update(newrole=default_role.id)


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0031_auto_20180815_0817'),
    ]

    operations = [
            migrations.RunPython(update_current_role_values)
    ]
