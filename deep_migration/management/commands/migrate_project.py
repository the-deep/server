from django.core.management.base import BaseCommand

from deep_migration.utils import (
    get_source_url,
    request_with_auth,
)
from deep_migration.models import ProjectMigration
from project.models import Project


EVENTS_URL = get_source_url('events')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        data = request_with_auth(EVENTS_URL)

        if not data or not data.get('data'):
            print('Couldn\'t find projects data at {}'.format(EVENTS_URL))

        projects = data['data']
        for project in projects:
            self.import_project(project)

    def import_project(self, data):
        print('------------')
        print('Migrating project')

        old_id = data['id']
        title = data['name']

        print('{} - {}'.format(old_id, title))

        migration, _ = ProjectMigration.objects.get_or_create(
            old_id=old_id,
        )
        if not migration.project:
            project = Project.objects.create(
                title=title,
            )
            migration.project = project
            migration.save()

        project = migration.project
        project.start_date = data['start_date']
        project.end_date = data['end_date']
        project.save()
