# Generated by Django 2.1.15 on 2020-05-19 09:15

import uuid
from django.db import migrations


def set_unique_value_to_questions(apps, schema_editor):
    """
    Set random name to provide unique names
    """
    Question = apps.get_model('questionnaire', 'Question')

    for question in Question.objects.all():
        question.name = str(uuid.uuid4())
        question.save()


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0006_auto_20200519_0913'),
    ]

    operations = [
        migrations.RunPython(set_unique_value_to_questions, reverse_code=migrations.RunPython.noop),
    ]
