from django.core.management.base import BaseCommand

from deep_migration.utils import (
    get_source_url,
    request_with_auth,
)
from deep_migration.models import (
    CountryMigration,
    ProjectMigration,
    UserMigration,
)
from project.models import Project, ProjectMembership

import reversion


EVENTS_URL = get_source_url('events2', 'v1')


def get_user(old_user_id):
    migration = UserMigration.objects.filter(old_id=old_user_id).first()
    return migration and migration.user


def get_region(reference_code):
    migration = CountryMigration.objects.filter(code=reference_code).first()
    return migration and migration.region


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        projects = request_with_auth(EVENTS_URL)

        if not projects:
            print('Couldn\'t find projects data at {}'.format(EVENTS_URL))

        with reversion.create_revision():
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

        for user_id in data['admins']:
            user = get_user(user_id)
            if user:
                ProjectMembership.objects.get_or_create(
                    project=project,
                    member=user,
                    defaults={'role': 'admin'},
                )

        for user_id in data['members']:
            user = get_user(user_id)
            if user:
                ProjectMembership.objects.get_or_create(
                    project=project,
                    member=user,
                    defaults={'role': 'normal'},
                )

        for region_code in data['countries']:
            region = get_region(region_code)
            if region and region not in project.regions.all():
                project.regions.add(region)
