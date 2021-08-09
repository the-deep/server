import autofixture

from reversion.models import Version

from deep.tests import TestCase
from project.models import Project
from user.models import User
from lead.models import Lead, LeadPreviewImage
from organization.models import Organization, OrganizationType
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
            tabular_field=field, entry_type=Entry.TagType.DATA_SERIES
        )
        return entry, field

    def test_search_filter_polygon(self):
        lead = self.create_lead()
        geo_widget = self.create(
            Widget,
            analysis_framework=lead.project.analysis_framework,
            widget_id=Widget.WidgetType.GEO,
            key='geoWidget-101',
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

        self.create_entry(lead=lead, entry_type=Entry.TagType.EXCERPT)
        self.create_entry(lead=lead, entry_type=Entry.TagType.IMAGE)
        self.create_entry(lead=lead, entry_type=Entry.TagType.DATA_SERIES)

        self.authenticate()
        self.post_filter_test(
            # Filter
            {'entry_type': [Entry.TagType.EXCERPT, Entry.TagType.IMAGE]},
            # Count
            Entry.objects.filter(entry_type__in=[Entry.TagType.EXCERPT, Entry.TagType.IMAGE]).count()
        )
        self.post_filter_test(
            # Filter
            {'entry_type': [Entry.TagType.EXCERPT]},
            # Count
            Entry.objects.filter(entry_type__in=[Entry.TagType.EXCERPT]).count()
        )
        self.post_filter_test(
            # Filter
            {'entry_type': [Entry.TagType.IMAGE, Entry.TagType.DATA_SERIES]},
            # Count
            Entry.objects.filter(entry_type__in=[Entry.TagType.IMAGE, Entry.TagType.DATA_SERIES]).count()
        )

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
        self.authenticate()
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
            widget_id=Widget.WidgetType.TEXT,
            key='text-102',
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
            widget_id=Widget.WidgetType.TEXT,
            key='text-103',
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
            widget_id=Widget.WidgetType.TEXT,
            key='text-104',
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
            widget_id=Widget.WidgetType.TEXT,
            key='text-105',
        )
        widget2 = self.create(
            Widget,
            analysis_framework=entry.lead.project.analysis_framework,
            widget_id=Widget.WidgetType.TEXT,
            key='text-106',
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

    def test_entry_options(self):
        url = '/api/v1/entry-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertIn('created_by', response.data)

    def test_entry_options_in_project(self):
        user1 = self.create_user()
        user2 = self.create_user()
        lead1 = self.create_lead()
        lead2 = self.create_lead()
        lead3 = self.create_lead()
        project1 = self.create(Project)
        project1.add_member(user1)
        project2 = self.create(Project)
        project2.add_member(user1)
        project2.add_member(user2)
        self.create(Entry, lead=lead1, project=project2, created_by=user1)
        self.create(Entry, lead=lead2, project=project2, created_by=user2)
        self.create(Entry, lead=lead3, project=project1, created_by=user2)

        # filter by project2
        url = f'/api/v1/entry-options/?project={project2.id}'
        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)
        # gives all the member of the project
        self.assertEqual(
            set([item['key'] for item in response.data['created_by']]),
            set([user1.id, user2.id])
        )

        # filter by project1
        url = f'/api/v1/entry-options/?project={project1.id}'
        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)
        # gives all the member of the project
        self.assertEqual(user1.id, response.data['created_by'][0]['key'])
        self.assertEqual(len(response.data['created_by']), 1)

    def filter_test(self, params, count=1):
        url = '/api/v1/entries/?{}'.format(params)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        r_data = response.json()
        self.assertEqual(len(r_data['results']), count)

    def post_filter_test(self, filters, count=1, skip_auth=False):
        return super().post_filter_test('/api/v1/entries/filter/', filters, count=count, skip_auth=False)

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
            filter_type=Filter.FilterType.NUMBER,
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
            filter_type=Filter.FilterType.LIST,
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
        self.authenticate()
        self.post_filter_test(filters, 2)

        # simulate filter behaviour of today from the frontend
        filters = {
            'lead_published_on__gte': '2020-09-25',
            'lead_published_on__lt': '2020-09-26',
        }
        self.post_filter_test(filters, 1)

    def test_lead_assignee_filter(self):
        another_user = self.create(User)
        lead1 = self.create_lead()
        lead1.assignee.add(self.user.pk)
        lead2 = self.create_lead()
        lead2.assignee.add(another_user.pk)
        lead3 = self.create_lead()
        lead3.assignee.add(self.user.pk)

        self.create_entry(lead=lead1)
        self.create_entry(lead=lead1)
        self.create_entry(lead=lead1)

        self.create_entry(lead=lead2)
        self.create_entry(lead=lead2)

        self.create_entry(lead=lead3)

        # test assignee created by self user
        filters = {
            'lead_assignee': [self.user.pk],
        }
        self.authenticate()
        self.post_filter_test(filters, 4)

        # test assignee created by another user
        filters = {
            'lead_assignee': [another_user.pk],
        }
        self.post_filter_test(filters, 2)

        # test assignee created by both users
        filters = {
            'lead_assignee': [self.user.pk, another_user.pk],
        }
        self.post_filter_test(filters, 6)

    def test_search_filter(self):
        entry, field = self.create_entry_with_data_series()
        filters = {
            'search': 'kadabra',
        }
        self.authenticate()
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

        current_version = Version.objects.get_for_object(entry).count()
        response = self.client.post(verify_url, {'version_id': current_version}, format='json')
        self.assert_200(response)
        entry.refresh_from_db()
        self.assertTrue(entry.verified)

        current_version = Version.objects.get_for_object(entry).count()
        response = self.client.post(unverify_url, {'version_id': current_version}, format='json')
        self.assert_200(response)
        response_data = response.json()
        assert response_data['id'] == entry.pk
        assert response_data['versionId'] != current_version
        assert response_data['versionId'] == current_version + 1
        entry.refresh_from_db()
        self.assertFalse(entry.verified)

        # With old current_version
        response = self.client.post(unverify_url, {'version_id': current_version}, format='json')
        self.assert_400(response)

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

    def test_authoring_organization_filter(self):
        organization_type1 = self.create(OrganizationType, title="National")
        organization_type2 = self.create(OrganizationType, title="International")
        organization_type3 = self.create(OrganizationType, title="Government")

        organization1 = self.create(Organization, organization_type=organization_type1)
        organization2 = self.create(Organization, organization_type=organization_type2)
        organization3 = self.create(Organization, organization_type=organization_type3)
        organization4 = self.create(Organization, parent=organization1)

        # create lead
        lead = self.create_lead(authors=[organization1])
        lead1 = self.create_lead(authors=[organization2])
        lead2 = self.create_lead(authors=[organization3, organization2])
        lead3 = self.create_lead(authors=[organization4])

        # create entry
        self.create_entry(lead=lead)
        self.create_entry(lead=lead1)
        self.create_entry(lead=lead2)
        self.create_entry(lead=lead3)

        # Test for GET
        url = '/api/v1/entries/?authoring_organization_types={}'

        self.authenticate()
        response = self.client.get(url.format(organization_type1.id))
        self.assert_200(response)
        assert len(response.data['results']) == 2, "There should be 2 entry"

        # get multiple leads
        organization_type_query = ','.join([
            str(id) for id in [organization_type1.id, organization_type3.id]
        ])
        response = self.client.get(url.format(organization_type_query))
        assert len(response.data['results']) == 3, "There should be 3 entry"

        # filter single post
        filters = {
            'authoring_organization_types': [organization_type1.id],
        }
        self.post_filter_test(filters, 2)

        filters = {
            'authoring_organization_types': [organization_type1.id, organization_type3.id]
        }
        self.post_filter_test(filters, 3)

    def test_entry_image_validation(self):
        lead = self.create_lead()
        user = self.create_user()
        lead.project.add_member(user, role=self.normal_role)

        url = '/api/v1/entries/'
        data = {
            'lead': lead.pk,
            'project': lead.project.pk,
            'analysis_framework': lead.project.analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': {},
        }

        self.authenticate()
        image = self.create_gallery_file()

        # Using raw image
        data['image_raw'] = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='  # noqa: E501
        response = self.client.post(url, data)
        self.assert_201(response)
        assert 'image' in response.data
        assert 'image_details' in response.data
        data.pop('image_raw')

        # Try to update entry with another user. we don't want 400 here as we are not updating image
        self.authenticate(user)
        response = self.client.patch(f"{url}{response.data['id']}/", {'attributes': {}})
        self.assert_200(response)
        assert 'image' in response.data
        assert 'image_details' in response.data

        self.authenticate()
        # Using lead image (same lead)
        data['lead_image'] = self.create(LeadPreviewImage, lead=lead, file=image.file).pk
        response = self.client.post(url, data)
        self.assert_201(response)
        assert 'image' in response.data
        assert 'image_details' in response.data
        data.pop('lead_image')

        # Using lead image (different lead)
        data['lead_image'] = self.create(LeadPreviewImage, lead=self.create_lead(), file=image.file).pk
        response = self.client.post(url, data)
        self.assert_400(response)
        data.pop('lead_image')

        # Using gallery file (owned)
        data['image'] = image.pk
        response = self.client.post(url, data)
        self.assert_201(response)
        assert 'image' in response.data
        assert 'image_details' in response.data
        data.pop('image')

        # Using gallery file (not owned)
        image.created_by = self.root_user
        image.is_public = False
        image.save()
        data['image'] = image.pk
        response = self.client.post(url, data)
        self.assert_400(response)
        data.pop('image')

        # Using gallery file (not owned but public)
        image.is_public = True
        image.save()
        data['image'] = image.pk
        response = self.client.post(url, data)
        self.assert_201(response)
        data.pop('image')
    # TODO: test export data and filter data apis

    def test_entry_id_filter(self):
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        entry1 = self.create_entry(project=project)
        entry2 = self.create_entry(project=project)
        entry3 = self.create_entry()

        self.authenticate(user)
        # only the entry of project that user is member
        self.post_filter_test({'entries_id': [entry1.pk, entry3.pk]}, 1, skip_auth=False)

        # try filtering out the entries that the user is not member of
        # Only the entry of project that user is member
        self.post_filter_test({'entries_id': [entry1.pk, entry2.pk, entry3.pk]}, 2, skip_auth=False)

        # try authenticating with default user created with project
        self.authenticate()
        # There should be 3 the entry
        self.post_filter_test({'entries_id': [entry1.pk, entry2.pk, entry3.pk]}, 3, skip_auth=False)


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
        entry = self.create_entry(image=None, image_raw='')
        assert entry.get_image_url() is None

    def test_entry_image(self):
        entry_image_url = '/some/path'
        file = File.objects.get(id=self.file.id)
        entry_with_raw_image = self.create_entry(
            image=None,
            image_raw='{}/{}'.format(entry_image_url, file.id)
        )
        entry_with_image = self.create_entry(image=File.objects.get(id=file.id))
        assert entry_with_raw_image.get_image_url() == file.get_file_url()
        assert entry_with_image.get_image_url() == file.get_file_url()

    def test_list_entries_summary(self):
        org_type1 = self.create(OrganizationType)
        org_type2 = self.create(OrganizationType)
        org1 = self.create(Organization, organization_type=org_type1)
        org2 = self.create(Organization, organization_type=org_type1)
        org3 = self.create(Organization, organization_type=org_type2)
        org4 = self.create(Organization, organization_type=org_type2)
        org5 = self.create(Organization, organization_type=None)

        lead1 = self.create_lead(source=org1)
        lead1.authors.set([org1, org4])
        lead2 = self.create_lead(source=org3)
        lead2.authors.set([org1, org2, org5])
        self.create_lead(source=org3)

        self.create_entry(lead=lead1)
        self.create_entry(lead=lead1)
        self.create_entry(lead=lead2)
        self.create_entry(lead=lead2)
        self.create_entry(lead=lead2)

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
        self.assertEqual(summ['totalSources'], len({org1, org3}))

        self.assertTrue({'org': {'id': org_type1.id, 'shortName': org_type1.short_name, 'title': org_type1.title}, 'count': 2} in summ['orgTypeCount'])  # noqa: E501
        self.assertTrue({'org': {'id': org_type2.id, 'shortName': org_type2.short_name, 'title': org_type2.title}, 'count': 1} in summ['orgTypeCount'])  # noqa: E501

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
        self.assertEqual(summ['totalSources'], len({org1, org3}))
        self.assertTrue({'org': {'id': org_type1.id, 'shortName': org_type1.short_name, 'title': org_type1.title}, 'count': 2} in summ['orgTypeCount'])  # noqa: E501
        self.assertTrue({'org': {'id': org_type2.id, 'shortName': org_type2.short_name, 'title': org_type2.title}, 'count': 1} in summ['orgTypeCount'])  # noqa: E501
