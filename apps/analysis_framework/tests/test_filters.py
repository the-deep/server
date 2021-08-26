from utils.graphene.tests import GraphQLTestCase

from analysis_framework.filter_set import AnalysisFrameworkGqFilterSet
from analysis_framework.factories import AnalysisFrameworkFactory


class TestAnalysisFrameworkFilter(GraphQLTestCase):
    def setUp(self) -> None:
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
