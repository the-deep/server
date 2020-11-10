from deep.tests import TestCase
import autofixture

from django.conf import settings
from project.models import Project
from user.models import User
from lead.models import Lead
from organization.models import Organization
from analysis_framework.models import (
    AnalysisFramework, Widget, Filter
)
from entry.models import (
    Entry,
    Attribute,
    FilterData,
    ProjectEntryLabel,
    LeadEntryGroup,
    EntryGroupLabel,
)

from gallery.models import File
from tabular.models import Sheet, Field


class EntryTests(TestCase):
    def create_entry_with_data_series(self):
        sheet = autofixture.create_one(Sheet, generate_fk=True)
        series = [  # create some dummy values
            {
                'value': 'male', 'processed_value': 'male',
                'invalid': False, 'empty': False
            },
            {
                'value': 'female', 'processed_value': 'female',
                'invalid': False, 'empty': False
            },
            {
                'value': 'female', 'processed_value': 'female',
                'invalid': False, 'empty': False
            },
        ]
        cache_series = [
            {'value': 'male', 'count': 1},
            {'value': 'female', 'count': 2},
        ]
        health_stats = {
            'invalid': 10,
            'total': 20,
            'empty': 10,
        }

        field = autofixture.create_one(
            Field,
            field_values={
                'sheet': sheet,
                'title': 'Abrakadabra',
                'type': Field.STRING,
                'data': series,
                'cache': {
                    'status': Field.CACHE_SUCCESS,
                    'series': cache_series,
                    'health_stats': health_stats,
                    'images': [],
                },
            }
        )

        entry = self.create_entry(
            tabular_field=field, entry_type=Entry.DATA_SERIES
        )
        return entry, field

    def test_search_filter_polygon(self):
        lead = self.create_lead()
        geo_widget = self.create(
            Widget,
            analysis_framework=lead.project.analysis_framework,
            widget_id='geoWidget',
            key='geoWidget-1312321321',
        )

        url = '/api/v1/entries/'
        data = {
            'lead': lead.pk,
            'project': lead.project.pk,
            'analysis_framework': geo_widget.analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': {
                geo_widget.pk: {
                    'data': {
                        'value': [1, 2, {'type': 'Point'}]
                    },
                },
            },
        }

        self.authenticate()
        self.client.post(url, data)
        data['attributes'][geo_widget.pk]['data']['value'] = [{'type': 'Polygon'}]
        self.client.post(url, data)
        data['attributes'][geo_widget.pk]['data']['value'] = [{'type': 'Line'}, {'type': 'Polygon'}]
        self.client.post(url, data)

        filters = {'geo_custom_shape': 'Point'}
        self.post_filter_test(filters, 1)
        filters['geo_custom_shape'] = 'Polygon'
        self.post_filter_test(filters, 2)
        filters['geo_custom_shape'] = 'Point,Line,Polygon'
        self.post_filter_test(filters, 3)
    
    def test_filter_entries_by_type(self):
        lead = self.create_lead()

        entry1 = self.create_entry(lead=lead, entry_type=Entry.EXCERPT)
        entry2 = self.create_entry(lead=lead, entry_type=Entry.IMAGE)
        entry3 = self.create_entry(lead=lead, entry_type=Entry.DATA_SERIES)

        self.post_filter_test({'entry_type': [Entry.EXCERPT, Entry.IMAGE]}, Entry.objects.filter(entry_type__in=[Entry.EXCERPT, Entry.IMAGE]).count())
        self.post_filter_test({'entry_type': [Entry.EXCERPT]}, Entry.objects.filter(entry_type__in=[Entry.EXCERPT]).count())
        self.post_filter_test({'entry_type': [Entry.IMAGE, Entry.DATA_SERIES]}, Entry.objects.filter(entry_type__in=[Entry.IMAGE, Entry.DATA_SERIES]).count())

    def test_search_filter_entry_group_label(self):
        lead = self.create_lead()
        project = lead.project

        # Entries
        entry1 = self.create_entry(lead=lead)
        entry2 = self.create_entry(lead=lead)

        # Labels
        label1 = self.create(ProjectEntryLabel, project=project, title='Label 1', order=1, color='#23f23a')
        label2 = self.create(ProjectEntryLabel, project=project, title='Label 2', order=2, color='#23f23a')

        # Groups
        group1 = self.create(LeadEntryGroup, lead=lead, title='Group 1', order=1)
        group2 = self.create(LeadEntryGroup, lead=lead, title='Group 2', order=2)
        group3 = self.create(LeadEntryGroup, lead=lead, title='Group 3', order=3)

        [
            self.create(EntryGroupLabel, group=group, label=label, entry=entry)
            for group, label, entry in [
                (group1, label1, entry1),
                (group1, label2, entry2),
                (group2, label1, entry2),
            ]
        ]

        default_filter = {'project': project.id}
        self.post_filter_test({**default_filter, 'project_entry_labels': [label1.pk]}, 2)
        self.post_filter_test({**default_filter, 'project_entry_labels': [label2.pk]}, 1)

        self.post_filter_test({**default_filter, 'lead_group_label': group1.title}, 2)
        self.post_filter_test({**default_filter, 'lead_group_label': 'Group'}, 2)
        self.post_filter_test({**default_filter, 'lead_group_label': group3.title}, 0)

    def test_create_entry(self):
        entry_count = Entry.objects.count()

        lead = self.create_lead()
        widget = self.create(
            Widget,
            analysis_framework=lead.project.analysis_framework,
        )

        url = '/api/v1/entries/'
        data = {
            'lead': lead.pk,
            'project': lead.project.pk,
            'analysis_framework': widget.analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': {
                widget.pk: {
                    'data': {'a': 'b'},
                },
            },
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        r_data = response.json()
        self.assertEqual(Entry.objects.count(), entry_count + 1)
        self.assertEqual(r_data['versionId'], 1)
        self.assertEqual(r_data['excerpt'], data['excerpt'])

        attributes = r_data['attributes']
        self.assertEqual(len(attributes.values()), 1)

        attribute = Attribute.objects.get(
            id=attributes[str(widget.pk)]['id']
        )

        self.assertEqual(attribute.widget.pk, widget.pk)
        self.assertEqual(attribute.data['a'], 'b')

        # Check if project matches
        entry = Entry.objects.get(id=r_data['id'])
        self.assertEqual(entry.project, entry.lead.project)

    def test_create_entry_no_project(self):
        """Even without project parameter, entry should be created(using project from lead)
        """
        entry_count = Entry.objects.count()
        lead = self.create_lead()

        widget = self.create(
            Widget,
            analysis_framework=lead.project.analysis_framework,
        )

        url = '/api/v1/entries/'
        data = {
            'lead': lead.pk,
            'analysis_framework': widget.analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': {
                widget.pk: {
                    'data': {'a': 'b'},
                },
            },
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        r_data = response.json()
        self.assertEqual(Entry.objects.count(), entry_count + 1)
        self.assertEqual(r_data['versionId'], 1)
        self.assertEqual(r_data['excerpt'], data['excerpt'])

        attributes = r_data['attributes']
        self.assertEqual(len(attributes.values()), 1)

        attribute = Attribute.objects.get(
            id=attributes[str(widget.pk)]['id']
        )

        self.assertEqual(attribute.widget.pk, widget.pk)
        self.assertEqual(attribute.data['a'], 'b')

        # Check if project matches
        entry = Entry.objects.get(id=r_data['id'])
        self.assertEqual(entry.project, entry.lead.project)

    def test_create_entry_no_perm(self):
        entry_count = Entry.objects.count()

        lead = self.create_lead()
        widget = self.create(
            Widget,
            analysis_framework=lead.project.analysis_framework,
        )

        user = self.create(User)
        lead.project.add_member(user, self.view_only_role)

        url = '/api/v1/entries/'
        data = {
            'lead': lead.pk,
            'project': lead.project.pk,
            'analysis_framework': widget.analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': {
                widget.pk: {
                    'data': {'a': 'b'},
                },
            },
        }

        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_403(response)

        self.assertEqual(Entry.objects.count(), entry_count)

    def test_delete_entry(self):
        entry = self.create_entry()

        url = '/api/v1/entries/{}/'.format(entry.id)

        self.authenticate()

        response = self.client.delete(url)
        self.assert_204(response)

    def test_delete_entry_no_perm(self):
        entry = self.create_entry()
        user = self.create(User)
        entry.project.add_member(user, self.view_only_role)

        url = '/api/v1/entries/{}/'.format(entry.id)

        self.authenticate(user)

        response = self.client.delete(url)
        self.assert_403(response)

    def test_duplicate_entry(self):
        entry_count = Entry.objects.count()
        lead = self.create_lead()

        client_id = 'randomId123'
        url = '/api/v1/entries/'
        data = {
            'lead': lead.pk,
            'project': lead.project.pk,
            'excerpt': 'Test excerpt',
            'analysis_framework': lead.project.analysis_framework.id,
            'client_id': client_id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        r_data = response.json()
        self.assertEqual(Entry.objects.count(), entry_count + 1)
        self.assertEqual(r_data['clientId'], client_id)
        id = r_data['id']

        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Entry.objects.count(), entry_count + 1)
        self.assertEqual(r_data['id'], id)
        self.assertEqual(r_data['clientId'], client_id)

    def test_patch_attributes(self):
        entry = self.create_entry()
        widget1 = self.create(
            Widget,
            analysis_framework=entry.lead.project.analysis_framework,
        )
        widget2 = self.create(
            Widget,
            analysis_framework=entry.lead.project.analysis_framework,
        )
        self.create(
            Attribute,
            data={'a': 'b'},
            widget=widget1,
        )

        url = '/api/v1/entries/{}/'.format(entry.id)
        data = {
            'attributes': {
                widget1.pk: {
                    'data': {'c': 'd'},
                },
                widget2.pk: {
                    'data': {'e': 'f'},
                }
            },
        }

        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_200(response)

        r_data = response.json()
        attributes = r_data['attributes']
        self.assertEqual(len(attributes.values()), 2)

        attribute1 = attributes[str(widget1.pk)]
        self.assertEqual(attribute1['data']['c'], 'd')
        attribute2 = attributes[str(widget2.pk)]
        self.assertEqual(attribute2['data']['e'], 'f')

    def test_options(self):
        url = '/api/v1/entry-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def filter_test(self, params, count=1):
        url = '/api/v1/entries/?{}'.format(params)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        r_data = response.json()
        self.assertEqual(len(r_data['results']), count)

    def post_filter_test(self, filters, count=1):
        url = '/api/v1/entries/filter/'
        params = {
            'filters': [[k, v] for k, v in filters.items()]
        }

        self.authenticate()
        response = self.client.post(url, params)
        self.assert_200(response)

        r_data = response.json()
        self.assertEqual(len(r_data['results']), count, f'Filters: {filters}')

    def both_filter_test(self, filters, count=1):
        self.filter_test(filters, count)

        k, v = filters.split('=')
        filters = {k: v}
        self.post_filter_test(filters, count)

    def test_filters(self):
        entry = self.create_entry()

        self.filter_test('verified=False', 1)
        self.filter_test('verified=True', 0)

        filter = self.create(
            Filter,
            analysis_framework=entry.analysis_framework,
            widget_key='test_filter',
            key='test_filter',
            title='Test Filter',
            filter_type=Filter.NUMBER,
        )
        self.create(FilterData, entry=entry, filter=filter, number=500)

        self.both_filter_test('test_filter=500')
        self.both_filter_test('test_filter__lt=600')
        self.both_filter_test('test_filter__gt=400')
        self.both_filter_test('test_filter__lt=400', 0)

        filter = self.create(
            Filter,
            analysis_framework=entry.analysis_framework,
            widget_key='test_list_filter',
            key='test_list_filter',
            title='Test List Filter',
            filter_type=Filter.LIST,
        )
        self.create(FilterData, entry=entry, filter=filter,
                    values=['abc', 'def', 'ghi'])

        self.both_filter_test('test_list_filter=abc')
        self.both_filter_test('test_list_filter=ghi,def', 1)
        self.both_filter_test('test_list_filter=uml,hij', 0)

        entry.excerpt = 'hello'
        entry.save()
        self.post_filter_test({'search': 'el'}, 1)
        self.post_filter_test({'search': 'pollo'}, 0)

    def test_lead_published_on_filter(self):
        lead1 = self.create_lead(published_on='2020-09-25')
        lead2 = self.create_lead(published_on='2020-09-26')
        lead3 = self.create_lead(published_on='2020-09-27')

        self.create_entry(lead=lead1)
        self.create_entry(lead=lead2)
        self.create_entry(lead=lead3)

        filters = {
            'lead_published_on__gte': '2020-09-25',
            'lead_published_on__lte': '2020-09-26',
        }
        url = '/api/v1/entries/filter/'
        params = {
            'filters': [[k, v] for k, v in filters.items()]
        }

        self.authenticate()
        response = self.client.post(url, params)

        self.assert_200(response)
        assert len(response.json()['results']) == 2

        # simulate filter behaviour of today from the frontend
        filters = {
            'lead_published_on__gte': '2020-09-25',
            'lead_published_on__lt': '2020-09-26',
        }
        url = '/api/v1/entries/filter/'
        params = {
            'filters': [[k, v] for k, v in filters.items()]
        }

        self.authenticate()
        response = self.client.post(url, params)

        self.assert_200(response)
        assert len(response.json()['results']) == 1

    def test_search_filter(self):
        entry, field = self.create_entry_with_data_series()
        filters = {
            'search': 'kadabra',
        }
        self.post_filter_test(filters)  # Should have single result

        filters = {
            'comment_status': 'resolved',
            'comment_assignee': self.user.pk,
            'comment_created_by': self.user.pk,
        }
        self.post_filter_test(filters, 0)  # Should have no result

        filters['comment_status'] = 'unresolved'
        self.post_filter_test(filters, 0)  # Should have no result

    def test_project_label_api(self):
        project = self.create_project(is_private=True)

        label1 = self.create(ProjectEntryLabel, project=project, title='Label 1', color='color', order=1)
        label2 = self.create(ProjectEntryLabel, project=project, title='Label 2', color='color', order=2)
        label3 = self.create(ProjectEntryLabel, project=project, title='Label 3', color='color', order=3)

        # Non member user
        self.authenticate(self.create_user())
        url = f'/api/v1/projects/{project.pk}/entry-labels/'
        response = self.client.get(url)
        self.assert_403(response)

        # List API
        self.authenticate()
        url = f'/api/v1/projects/{project.pk}/entry-labels/'
        response = self.client.get(url)
        assert len(response.json()['results']) == 3

        # Bulk update API
        url = f'/api/v1/projects/{project.pk}/entry-labels/bulk-update-order/'
        order_data = [
            {'id': label1.pk, 'order': 3},
            {'id': label2.pk, 'order': 2},
            {'id': label3.pk, 'order': 1},
        ]
        response = self.client.post(url, order_data)
        self.assertEqual(
            {d['id']: d['order'] for d in order_data},
            {d['id']: d['order'] for d in response.json()}
        )

    def test_verify_entry(self):
        entry = self.create_entry()
        user = self.create(User)
        entry.project.add_member(user, self.view_only_role)
        verify_url = '/api/v1/entries/{}/verify/'.format(entry.id)
        unverify_url = '/api/v1/entries/{}/unverify/'.format(entry.id)

        self.authenticate(user)

        response = self.client.post(verify_url)
        self.assert_403(response)

        # normal role
        user = self.create(User)
        entry.project.add_member(user, self.normal_role)
        self.authenticate()
        response = self.client.post(verify_url)
        self.assert_200(response)
        entry.refresh_from_db()
        self.assertTrue(entry.verified)
        response = self.client.post(unverify_url)
        self.assert_200(response)
        entry.refresh_from_db()
        self.assertFalse(entry.verified)

    def test_update_entry_unverifies_verified_entry(self):
        entry = self.create_entry(verified=True)
        self.assertTrue(entry.verified)

        url = '/api/v1/entries/{}/'.format(entry.id)
        data = {
            'excerpt': 'updated...'
        }

        self.authenticate()
        response = self.client.patch(url, data)
        self.assert_200(response)
        entry.refresh_from_db()
        self.assertFalse(entry.verified)

    # TODO: test export data and filter data apis


class EntryTest(TestCase):
    def setUp(self):
        super().setUp()
        self.file = File.objects.create(title='test')

    def create_project(self):
        analysis_framework = self.create(AnalysisFramework)
        return self.create(
            Project, analysis_framework=analysis_framework,
            role=self.admin_role
        )

    def create_lead(self, **fields):
        project = self.create_project()
        return self.create(Lead, project=project, **fields)

    def create_entry(self, **fields):
        lead = fields.pop('lead', self.create_lead())
        return self.create(
            Entry, lead=lead, project=lead.project,
            analysis_framework=lead.project.analysis_framework,
            **fields
        )

    def test_entry_no_image(self):
        entry = self.create_entry(image='')
        assert entry.get_image_url() is None

    def test_entry_image(self):
        entry_image_url = '/some/path'
        entry = self.create_entry(
            image='{}/{}'.format(entry_image_url, self.file.id)
        )
        assert entry.get_image_url() is not None
        # Get file again, because it won't have random_string updated
        file = File.objects.get(id=self.file.id)
        assert entry.get_image_url() == '{protocol}://{domain}{url}'.format(
            protocol=settings.HTTP_PROTOCOL,
            domain=settings.DJANGO_API_HOST,
            url='/private-file/{uuid}/{filename}'.format(**{
                'uuid': file.uuid,
                'filename': file.title,
            }
            ),
        )

    def test_list_entries_summary(self):
        org1 = self.create(Organization)
        org2 = self.create(Organization)
        org3 = self.create(Organization)
        org4 = self.create(Organization)
        org5 = self.create(Organization)

        lead1 = self.create_lead(source=org1)
        lead1.authors.set([org1, org4])
        lead2 = self.create_lead(source=org3)
        lead2.authors.set([org1, org2])
        lead3 = self.create_lead(source=org3)

        entry1 = self.create_entry(lead=lead1)
        entry2 = self.create_entry(lead=lead1)
        entry3 = self.create_entry(lead=lead2)
        entry4 = self.create_entry(lead=lead2)
        entry5 = self.create_entry(lead=lead2)

        url = '/api/v1/entries/filter/'

        self.authenticate()
        response = self.client.post(url, dict(calculate_summary='1'))
        self.assert_200(response)
        r_data = response.json()
        self.assertIn('summary', r_data)
        summ = r_data['summary']
        self.assertEqual(summ['totalVerifiedEntries'], Entry.objects.filter(verified=True).count())
        self.assertEqual(summ['totalUnverifiedEntries'], Entry.objects.filter(verified=False).count())
        self.assertEqual(summ['totalLeads'], len([lead1, lead2]))
        self.assertEqual(summ['totalUniqueAuthors'], len({org1.organization_type,
                                                          org2.organization_type,
                                                          org4.organization_type}))
        self.assertEqual(summ['totalSources'], len({org1, org3}))

        url = '/api/v1/entries/?calculate_summary=1'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        r_data = response.json()
        self.assertIn('summary', r_data)
        summ = r_data['summary']
        self.assertEqual(summ['totalVerifiedEntries'], Entry.objects.filter(verified=True).count())
        self.assertEqual(summ['totalUnverifiedEntries'], Entry.objects.filter(verified=False).count())
        self.assertEqual(summ['totalLeads'], len([lead1, lead2]))
        self.assertEqual(summ['totalUniqueAuthors'], len({org1.organization_type,
                                                          org2.organization_type,
                                                          org4.organization_type}))
        self.assertEqual(summ['totalSources'], len({org1, org3}))
