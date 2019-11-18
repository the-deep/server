from django.db import transaction
from django.core.management.base import BaseCommand
from django.core import files
from io import BytesIO

from organization.models import (
    OrganizationType,
    Organization,
)
from geo.models import Region
from gallery.models import File

import requests


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--sync-by-name',
            action='store_true',
            help='Sync using short name ( Used for existing organization without relief web id)',
        )

    def handle(self, *args, **kwargs):
        self.sync_by_name = kwargs['sync_by_name']
        self.fetch_org_types()
        self.fetch_organizations()

    def fetch_org_types(self):
        print('Fetching organization types')
        URL = 'https://api.reliefweb.int/v1/references/organization-types'
        response = requests.get(URL).json()

        print('Loading organization types')
        total = len(response['data'])
        for i, type_data in enumerate(response['data']):
            self.load_org_type(type_data)
            print('{} out of {}'.format(i + 1, total))

    def load_org_type(self, type_data):
        fields = type_data['fields']
        values = {
            'description': fields.get('description', ''),
            'relief_web_id': fields.get('id'),
        }

        OrganizationType.objects.update_or_create(
            title=fields['name'],
            defaults=values
        )

    @transaction.atomic
    def fetch_organizations(self, offset=0, limit=1000):
        print('Fetching organizations starting from: {}'.format(offset))
        URL = 'https://api.reliefweb.int/v1/sources?fields[include][]=logo&fields[include][]=country.iso3&fields[include][]=shortname&fields[include][]=longname&fields[include][]=homepage&fields[include][]=type&offset={}&limit={}'.format( # noqa
            offset,
            limit,
        )
        response = requests.get(URL).json()

        print('Loading organizations')
        total = response['totalCount']
        for i, org_data in enumerate(response['data']):
            print('{} out of {}'.format(i + offset + 1, total))
            self.load_organization(org_data)

        if len(response['data']) > 0:
            self.fetch_organizations(offset + limit, limit)

    def _get_organization_type_by_relief_web_id(self, relief_web_id):
        if not hasattr(self, '_organization_types'):
            self._organization_types = {
                org.relief_web_id or 'n/a': org
                for org in OrganizationType.objects.all()
            }
        return self._organization_types.get(relief_web_id)

    def load_organization(self, org_data):
        fields = org_data['fields']
        values = {
            'title': fields['name'],
            'short_name': fields.get('shortname', ''),
            'long_name': fields.get('longname', ''),
            'url': fields.get('homepage', ''),
            'relief_web_id': org_data['id'],
            'verified': True,
            'organization_type': self._get_organization_type_by_relief_web_id(
                fields.get('type', {}).get('id')
            ),
        }

        organization, created = Organization.objects.update_or_create(
            **(
                # Use short_name to sync (Should only be used once) --sync-by-name
                {'title': values['title'], 'created_by': None}
                if self.sync_by_name
                # Using relief_web_id to sync
                else {'relief_web_id': values['relief_web_id']}
            ),
            defaults=values,
        )

        countries = fields.get('country', [])
        for country in countries:
            code = country.get('iso3')
            if not code:
                continue

            region = Region.objects.filter(
                public=True,
                code=code,
            ).first()
            if not region:
                continue

            organization.regions.add(region)

        if created or not fields.get('logo'):
            return

        logo_data = fields['logo']

        resp = requests.get(logo_data['url'])
        fp = BytesIO()
        fp.write(resp.content)

        logo = File.objects.create(
            is_public=True,
            title=logo_data['filename'],
            mime_type=logo_data['mimetype'],
        )
        logo.file.save(logo_data['filename'], files.File(fp))

        organization.logo = logo
        organization.save()
