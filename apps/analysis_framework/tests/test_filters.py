from datetime import timedelta
from unittest.mock import patch
from utils.graphene.tests import GraphQLTestCase

from analysis_framework.filter_set import AnalysisFrameworkGqFilterSet
from analysis_framework.factories import AnalysisFrameworkFactory
from entry.factories import EntryFactory
from lead.factories import LeadFactory


class TestAnalysisFrameworkFilter(GraphQLTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.filter_class = AnalysisFrameworkGqFilterSet

    def test_search_filter(self):
        AnalysisFrameworkFactory.create(title='one')
        af2 = AnalysisFrameworkFactory.create(title='two')
        af3 = AnalysisFrameworkFactory.create(title='twoo')
        obtained = self.filter_class(data=dict(
            search='tw'
        )).qs
        expected = [af2, af3]
        self.assertQuerySetIdEqual(
            expected,
            obtained
        )

    @patch('django.utils.timezone.now')
    def test_filter_recently_used(self, now_patch):
        now = self.PATCHER_NOW_VALUE
        now_patch.side_effect = lambda: now - timedelta(days=90)
        af1, af2, af3, _ = AnalysisFrameworkFactory.create_batch(4)
        lead1, lead2 = LeadFactory.create_batch(2)
        # Within date range window
        EntryFactory.create(
            analysis_framework=af1,
            lead=lead1,
        )
        EntryFactory.create(
            analysis_framework=af2,
            lead=lead2,
        )
        # Outside date range window
        now_patch.side_effect = lambda: now - timedelta(days=190)
        EntryFactory.create(
            analysis_framework=af3,
            lead=lead1,
        )
        # Make sure we only get af1, af2
        now_patch.side_effect = lambda: now
        obtained = set(list(
            self
            .filter_class(data={'recently_used': True})
            .qs
            .values_list('id', flat=True)
        ))
        expected = set([af1.pk, af2.pk])
        self.assertEqual(obtained, expected)
