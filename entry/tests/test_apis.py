from deep.tests import TestCase

from project.models import Project
from lead.models import Lead
from analysis_framework.models import (
    AnalysisFramework, Widget, Filter
)
from entry.models import Entry, FilterData


class EntryTests(TestCase):
    def create_project(self):
        analysis_framework = self.create(AnalysisFramework)
        return self.create(Project, analysis_framework=analysis_framework)

    def create_lead(self):
        project = self.create_project()
        return self.create(Lead, project=project)

    def create_entry(self):
        lead = self.create_lead()
        return self.create(
            Entry, lead=lead,
            analysis_framework=lead.project.analysis_framework,
        )

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
            'analysis_framework': widget.analysis_framework.pk,
            'excerpt': 'This is test excerpt',
            'attributes': [
                {
                    'widget': widget.pk,
                    'data': {'a': 'b'},
                },
            ],
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Entry.objects.count(), entry_count + 1)
        self.assertEqual(response.data['version_id'], 1)
        self.assertEqual(response.data['excerpt'], data['excerpt'])
        self.assertEqual(response.data['attributes'][0]['widget'], widget.pk)
        self.assertEqual(response.data['attributes'][0]['data']['a'], 'b')

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

        self.assertEqual(len(response.data['results']['entries']), count)

    def post_filter_test(self, filters, count=1):
        url = '/api/v1/entries/filter/'
        params = {
            'filters': [[k, v] for k, v in filters.items()]
        }

        self.authenticate()
        response = self.client.post(url, params)
        self.assert_200(response)

        self.assertEqual(len(response.data['results']['entries']), count)

    def both_filter_test(self, filters, count=1):
        self.filter_test(filters, count)

        k, v = filters.split('=')
        filters = {k: v}
        self.post_filter_test(filters, count)

    def test_filters(self):
        entry = self.create_entry()

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

    # TODO: test export data and filter data apis
