# Generated by Django 2.1.15 on 2021-04-27 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0006_assignment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[
                ('project_join_request', 'Join project request'),
                ('project_join_request_abort', 'Join project request abort'),
                ('project_join_response', 'Join project response'),
                ('entry_comment_add', 'Entry Comment Add'),
                ('entry_comment_modify', 'Entry Comment Modify'),
                ('entry_comment_assignee_change', 'Entry Comment Assignee Change'),
                ('entry_comment_reply_add', 'Entry Comment Reply Add'),
                ('entry_comment_reply_modify', 'Entry Comment Reply Modify'),
                ('entry_comment_resolved', 'Entry Comment Resolved'),
                ('entry_review_comment_add', 'Entry Review Comment Add'),
                ('entry_review_comment_modify', 'Entry Review Comment Modify'),
            ], max_length=48),
        ),
    ]