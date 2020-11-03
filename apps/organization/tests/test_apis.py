from deep.tests import TestCase

from organization.models import Organization


class OrganizationTests(TestCase):
    def test_get_or_create_api(self):
        reliefweb = Organization.objects.create(
            title='Relief WEB',
            short_name='reliefweb',
        )
        togglecorp = Organization.objects.create(
            title='Togglecorp',
            short_name='togglecorp',
        )
        dfs = Organization.objects.create(
            title='dfs',
            short_name='dfs',
        )
        Organization.objects.create(title='cyclical', short_name='cyclical', parent=dfs)

        organizations_required = {
            'reliefweb': reliefweb,
            'togglecorp': togglecorp,
            'dfs': dfs,
            'cyclical': dfs,
        }
        url = '/api/v1/organizations/get-or-create/'
        data = {
            'organizations': organizations_required.keys(),
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_200(response)
        for org_resp in response.json()['results']:
            self.assertEqual(
                organizations_required[org_resp['key']].id,
                org_resp['organization']['id'],
            )
