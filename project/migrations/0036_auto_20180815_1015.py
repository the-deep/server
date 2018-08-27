# -*- coding: utf-8 -*-
# Created by bewakes
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def update_is_directly_added(apps, schema_editor):
    ProjectMembership = apps.get_model('project', 'ProjectMembership')
    ProjectMembership.objects.all().update(is_directly_added=True)


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0035_auto_20180815_1014'),
    ]

    operations = [
        migrations.RunPython(update_is_directly_added)
    ]
