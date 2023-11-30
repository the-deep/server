from django.db import migrations


def set_is_assessment_enabled_true(apps, schema_editor):
    Project = apps.get_model('project', 'Project')
    Project.objects.filter(
        assessment_template__isnull=False
    ).update(
        is_assessment_enabled=True
    )


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0004_project_is_assessment_enabled'),
    ]

    operations = [
        migrations.RunPython(
            set_is_assessment_enabled_true,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
