from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
import requests

from deep_migration.utils import (
    get_source_url,
    get_migrated_gallery_file,
)

from deep_migration.models import UserMigration


USERS_URL = get_source_url('users2', 'v1')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        data = requests.get(USERS_URL).json()

        if not data:
            print('Couldn\'t find users data at {}'.format(USERS_URL))
            return

        for user in data:
            self.import_user(user)

    def import_user(self, data):
        print('------------')
        print('Migrating user')

        old_id = data['id']
        username = data['username']
        email = data['email']

        first_name = data['first_name']
        last_name = data['last_name']

        print('{} - {} {}'.format(old_id, first_name, last_name))

        migration, _ = UserMigration.objects.get_or_create(
            old_id=old_id,
        )
        if not migration.user:
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.create_user(
                    username=username,
                )
            migration.user = user
            migration.save()

        user = migration.user
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name

        user.profile.organization = data['organization']
        user.profile.display_picture = get_migrated_gallery_file(
            data['photo']
        )
        user.profile.hid = data['hid']
        user.save()

        return user
