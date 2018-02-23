from rest_framework import status
from rest_framework.test import APITestCase

from user.tests.test_apis import AuthMixin
from lead.tests.test_apis import LeadMixin
from project.tests.test_apis import ProjectMixin

from analysis_framework.tests.test_apis import (
    AnalysisFrameworkMixin, WidgetMixin,
    FilterMixin, ExportableMixin
)
from entry.models import (
    Entry, Attribute, FilterData, ExportData
)
from analysis_framework.models import Filter


# Mixins

class EntryMixin():
    """
    Entry mixin
    """
    def create_or_get_entry(self):
        """
        Create or get entry
        Required mixin: LeadMixin, ProjectMixin, AnalysisFrameworkMixin
        """
        entry = Entry.objects.first()
        if not entry:
            lead = self.create_or_get_lead()
            analysis_framework = self.create_or_get_analysis_framework()
            entry = Entry.objects.create(
                lead=lead,
                analysis_framework=analysis_framework,
            )
        return entry


class AttributeMixin():
    """
    Attribute mixin
    """
    def create_or_get_attribute(self):
        """
        Create or get  attribute
        """
        attribute = Attribute.objects.first()
        if not attribute:
            entry = self.create_or_get_entry()
            widget = self.create_or_widget()
            entry = Entry.objects.create(
                entry=entry,
                widget=widget,
            )
        return attribute


class FilterDataMixin():
    """
    Filter Data mixin
    """
    def create_or_get_filter_data(self):
        """
        Create or get filter data
        """
        filter_data = FilterData.objects.first()
        if not filter_data:
            entry = self.create_or_get_entry()
            filter = self.create_or_get_filter()
            values = []
            filter_data = FilterData.objects.create(
                entry=entry,
                filter=filter,
                values=values
            )
        return filter_data


class ExportDataMixin():
    """
    Export Data Mixin
    """
    def create_or_get_export_data(self):
        """
        Create or get export data
        """
        export_data = ExportData.objects.first()
        if not export_data:
            entry = self.create_or_get_entry()
            exportable = self.create_or_get_exportable()
            export_data = ExportData.objects.create(
                entry=entry,
                exportable=exportable
            )
        return export_data


# Tests

class EntryTests(AuthMixin, EntryMixin, LeadMixin, ProjectMixin,
                 AnalysisFrameworkMixin, WidgetMixin, APITestCase):
    """
    Entry Tests
    """
    # TODO: Add Image Test
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_entry(self):
        """
        Create Entry Test
        """
        old_count = Entry.objects.count()
        analysis_framework = self.create_or_get_analysis_framework()
        widget = self.create_or_get_widget()

        url = '/api/v1/entries/'
        data = {
            'lead': self.create_or_get_lead().pk,
            'analysis_framework': analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': [
                {
                    'widget': widget.pk,
                    'data': {'a': 'b'},
                },
            ],
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Entry.objects.count(), old_count + 1)
        self.assertEqual(response.data['version_id'], 1)
        self.assertEqual(response.data['excerpt'], data['excerpt'])
        self.assertEqual(response.data['attributes'][0]['widget'], widget.pk)
        self.assertEqual(response.data['attributes'][0]['data']['a'], 'b')

    def test_options(self):
        """
        Options api
        """
        url = '/api/v1/entry-options/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def filter_test(self, params, count=1):
        """
        Request to `url?params` and check if given count of
        data returns.
        """
        url = '/api/v1/entries/?{}'.format(params)
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']['entries']), count)

    def post_filter_test(self, filters, count=1):
        """
        Similar to above but this time pass filter params as post body
        """
        url = '/api/v1/entries/filter/'
        params = {
            'filters': [[k, v] for k, v in filters.items()]
        }
        response = self.client.post(url, params,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']['entries']), count)

    def test_filters(self):
        """
        Add some filter data to the entry and test the
        GET apis with filter params
        """
        entry = self.create_or_get_entry()

        filter = Filter.objects.create(
            analysis_framework=entry.analysis_framework,
            widget_key='test_filter',
            key='test_filter',
            title='Test Filter',
            filter_type=Filter.NUMBER,
        )
        FilterData.objects.create(
            entry=entry,
            filter=filter,
            number=500,
        )

        self.filter_test('test_filter=500')
        self.filter_test('test_filter__lt=600')
        self.filter_test('test_filter__gt=400')
        self.filter_test('test_filter__lt=400', 0)

        filter = Filter.objects.create(
            analysis_framework=entry.analysis_framework,
            widget_key='test_list_filter',
            key='test_list_filter',
            title='Test List Filter',
            filter_type=Filter.LIST,
        )
        FilterData.objects.create(
            entry=entry,
            filter=filter,
            values=['abc', 'def', 'ghi'],
        )

        self.filter_test('test_list_filter=abc')
        self.filter_test('test_list_filter=ghi,def', 1)
        self.filter_test('test_list_filter=uml,hij', 0)

    def test_post_filters(self):
        """
        Add some filter data to the entry and test the
        POST entry/filters api
        """
        entry = self.create_or_get_entry()

        filter = Filter.objects.create(
            analysis_framework=entry.analysis_framework,
            widget_key='test_list_filter',
            key='test_filter',
            title='Test Filter',
            filter_type=Filter.NUMBER,
        )
        FilterData.objects.create(
            entry=entry,
            filter=filter,
            number=500,
        )

        self.post_filter_test({'test_filter': 500})
        self.post_filter_test({'test_filter__lt': 600})
        self.post_filter_test({'test_filter__gt': 400})
        self.post_filter_test({'test_filter__lt': 400}, 0)

        filter = Filter.objects.create(
            analysis_framework=entry.analysis_framework,
            widget_key='test_list_filter',
            key='test_list_filter',
            title='Test List Filter',
            filter_type=Filter.LIST,
        )
        FilterData.objects.create(
            entry=entry,
            filter=filter,
            values=['abc', 'def', 'ghi'],
        )

        self.post_filter_test({'test_list_filter': 'abc'})
        self.post_filter_test({'test_list_filter': 'ghi,def'})
        self.post_filter_test({'test_list_filter': 'uml,hij'}, 0)

        entry.excerpt = 'hello'
        entry.save()
        self.post_filter_test({'search': 'el'}, 1)
        self.post_filter_test({'search': 'pollo'}, 0)


class AttributeTests(AuthMixin, EntryMixin, LeadMixin, ProjectMixin,
                     AnalysisFrameworkMixin, WidgetMixin, APITestCase):
    """
    Attribute Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_attribute(self):
        """
        Create Attribute Test
        """
        # TODO: Add Better data
        old_count = Attribute.objects.count()
        url = '/api/v1/entry-attributes/'
        data = {
            'entry': self.create_or_get_entry().pk,
            'widget': self.create_or_get_widget().pk,
            'data': {},
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Attribute.objects.count(), old_count + 1)
        self.assertEqual(response.data['data'], data['data'])


class FilterDataTests(AuthMixin, EntryMixin, LeadMixin, ProjectMixin,
                      AnalysisFrameworkMixin, WidgetMixin,
                      FilterMixin, APITestCase):
    """
    Filter Data Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_filter_data(self):
        """
        Create Filter Test
        """
        # TODO: Add Better values and number
        old_count = FilterData.objects.count()
        url = '/api/v1/entry-filter-data/'
        data = {
            'entry': self.create_or_get_entry().pk,
            'filter': self.create_or_get_filter().pk,
            'values': [],
            'number': 12,
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FilterData.objects.count(), old_count + 1)
        self.assertEqual(response.data['values'], data['values'])
        self.assertEqual(response.data['number'], data['number'])


class ExportDataTests(AuthMixin, EntryMixin, LeadMixin, ProjectMixin,
                      AnalysisFrameworkMixin, WidgetMixin, ExportableMixin,
                      FilterMixin, APITestCase):
    """
    Export Data Tests
    """
    def setUp(self):
        """
        Get HTTP_AUTHORIZATION Header
        """
        self.auth = self.get_auth()

    def test_create_export_data(self):
        """
        Create Export Data Test
        """
        # TODO: Add Better values and number
        old_count = ExportData.objects.count()
        url = '/api/v1/entry-export-data/'
        data = {
            'entry': self.create_or_get_entry().pk,
            'exportable': self.create_or_get_exportable().pk,
            'data': {},
        }

        response = self.client.post(url, data,
                                    HTTP_AUTHORIZATION=self.auth,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExportData.objects.count(), old_count + 1)
        self.assertEqual(response.data['data'], data['data'])
