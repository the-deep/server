from deep_migration.utils import (
    MigrationCommand,
    get_source_url,
    request_with_auth,
    get_migrated_gallery_file,
)

from deep_migration.models import (
    UserGroupMigration,
    UserMigration,
    ProjectMigration,
)
from user_group.models import (
    UserGroup,
    GroupMembership,
)

import reversion


def get_user(old_user_id):
    migration = UserMigration.objects.filter(old_id=old_user_id).first()
    return migration and migration.user


def get_project(project_id):
    migration = ProjectMigration.objects.filter(old_id=project_id).first()
    return migration and migration.project


class Command(MigrationCommand):
    def run(self):
        user_groups = request_with_auth(get_source_url('user-groups', 'v1'))

        if not user_groups:
            print('Couldn\'t find user groups data')

        with reversion.create_revision():
            for user_group in user_groups:
                self.import_user_group(user_group)

    def import_user_group(self, data):
        print('------------')
        print('Migrating user group')

        old_id = data['id']
        title = data['name']

        print('{} - {}'.format(old_id, title))

        migration, _ = UserGroupMigration.objects.get_or_create(
            old_id=old_id,
        )
        if not migration.user_group:
            user_group = UserGroup.objects.create(
                title=title,
            )
            migration.user_group = user_group
            migration.save()

        user_group = migration.user_group
        user_group.description = data['description']
        user_group.display_picture = get_migrated_gallery_file(
            data['photo']
        )
        user_group.global_crisis_monitoring = data['acaps']
        user_group.save()

        for user_id in data['admins']:
            user = get_user(user_id)
            if user:
                GroupMembership.objects.get_or_create(
                    group=user_group,
                    member=user,
                    defaults={'role': 'admin'},
                )

        for user_id in data['members']:
            user = get_user(user_id)
            if user:
                GroupMembership.objects.get_or_create(
                    group=user_group,
                    member=user,
                    defaults={'role': 'normal'},
                )

        for project_id in data['projects']:
            project = get_project(project_id)
            if project:
                project.user_groups.add(user_group)

        return user_group
