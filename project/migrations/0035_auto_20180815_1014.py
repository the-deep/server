# -*- coding: utf-8 -*-
# Created by bewakes
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0034_auto_20180815_1013'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectmembership',
            name='is_directly_added',
            field=models.BooleanField(default=False),
        ),
    ]
