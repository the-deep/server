
from django.db import migrations
from django.db.models import Count


def _rename_duplicate_name(Project):
    # NOTE: Assuming there are just 4-5k projects.
    project_title_qs = Project.objects.order_by().values('title').annotate(count=Count('id'))
    existing_project_titles = list(  # NOTE: High memory usages
        project_title_qs.values_list('title', flat=True).distinct()
    )
    existing_project_titles_lower = [title.lower() for title in existing_project_titles]
    title_projects_map = {}
    for title in existing_project_titles_lower:
        projects = Project.objects.filter(title__iexact=title)
        if projects.count() > 1:
            title_projects_map[title] = projects
    for title, projects in title_projects_map.items():
        index = 0
        for project in projects:
            while True:  # Or for loop.
                index += 1
                new_title = f"{project.title} ({str(index)})"
                if new_title.lower() not in existing_project_titles_lower:
                    existing_project_titles_lower.append(new_title.lower())
                    break
            project.title = new_title
            project.save(update_fields=('title',))


def rename_duplicate_name(apps, schema_editor):
    Project = apps.get_model('project', 'Project')
    _rename_duplicate_name(Project)


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0077_merge_0076_auto_20220520_0834_0076_auto_20220524_0523'),
    ]

    operations = [
        migrations.RunPython(
            rename_duplicate_name,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
