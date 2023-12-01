from django.db import migrations


def change_project_org_type_from_char_choice_to_integer_choice(apps, schema_editor):
    ProjectOrganization = apps.get_model('project', 'ProjectOrganization')

    project_org_map = {
        'lead_organization': 1,
        'international_partner': 2,
        'national_partner': 3,
        'donor': 4,
        'government': 5,
    }

    project_org = ProjectOrganization.objects.all()

    for org in project_org:
        org.organization_type = project_org_map[org.organization_type]
        org.save()


class Migration(migrations.Migration):

    dependencies = [
        ('project', 'set_is_assessment_enabled_true'),
    ]

    operations = [
        migrations.RunPython(
            change_project_org_type_from_char_choice_to_integer_choice,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
