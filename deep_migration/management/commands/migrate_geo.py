import requests

from deep_migration.utils import (
    MigrationCommand,
    get_source_url,
    get_migrated_gallery_file,
)

from geo.models import (
    Region,
    AdminLevel,
)
from deep_migration.models import (
    CountryMigration,
    AdminLevelMigration,
)

from geo.tasks import load_geo_areas


class Command(MigrationCommand):
    def run(self):
        data = requests.get(get_source_url('countries')).json()

        if not data or not data.get('data'):
            print('Couldn\'t find countries data')
            return

        countries = data['data']
        for country in countries:
            self.import_country(country)

    def import_country(self, country):
        print('------------')
        print('Migrating country')

        code = country['reference_code']
        modified_code = country['code']
        title = country['name']
        print('{} - {}'.format(code, title))

        public = (code == modified_code)

        migration, _ = CountryMigration.objects.get_or_create(
            code=modified_code,
        )
        if not migration.region:
            region = Region.objects.create(
                code=code,
                title=title,
            )
            migration.region = region
            migration.save()

        region = migration.region
        region.code = code
        region.title = title
        region.public = public

        region.regional_groups = country['regions']
        region.key_figures = country['key_figures']
        region.media_sources = country['media_sources']

        region.save()

        admin_levels = country['admin_levels']
        admin_levels.sort(key=lambda a: a['level'])
        parent = None
        for admin_level in admin_levels:
            parent = self.import_admin_level(region, parent, admin_level)

        load_geo_areas.delay(region.id)
        return region

    def import_admin_level(self, region, parent, data):
        print('Migrating admin level')

        old_id = data['id']
        title = data['name']
        level = data['level']

        print('{} - {}'.format(data['id'],
                               data['name']))

        migration, _ = AdminLevelMigration.objects.get_or_create(
            old_id=old_id
        )

        if not migration.admin_level:
            admin_level = AdminLevel.objects.create(
                region=region,
                parent=parent,
                title=title,
            )
            migration.admin_level = admin_level
            migration.save()

        admin_level = migration.admin_level
        admin_level.parent = parent
        admin_level.level = level
        admin_level.name_prop = data['property_name']
        admin_level.code_prop = data['property_pcode']
        if level > 0:
            admin_level.parent_name_prop = 'NAME_{}'.format(level - 1)
        admin_level.geo_shape_file = get_migrated_gallery_file(data['geojson'])
        admin_level.stale_geo_areas = True
        admin_level.save()

        return admin_level
