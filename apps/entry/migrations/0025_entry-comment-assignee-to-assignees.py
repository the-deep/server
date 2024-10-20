# Generated by Django 2.1.15 on 2020-06-30 07:04

from django.db import migrations


def copy_from_assignee_to_assignees(apps, schema_editor):
    EntryComment = apps.get_model('entry', 'EntryComment')
    for entry_comment in EntryComment.objects.filter(assignee__isnull=False).prefetch_related('assignee'):
        entry_comment.assignees.add(entry_comment.assignee)


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0024_auto_20200630_0702'),
    ]

    operations = [
        migrations.RunPython(copy_from_assignee_to_assignees)
    ]
