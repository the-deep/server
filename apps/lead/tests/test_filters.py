from lead.factories import LeadGroupFactory
from lead.filter_set import LeadGroupGQFilterSet
from project.factories import ProjectFactory

from utils.graphene.tests import GraphQLTestCase


class TestLeadGroupFilter(GraphQLTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.filter_class = LeadGroupGQFilterSet

    def test_search_filter(self):
        project = ProjectFactory.create()
        LeadGroupFactory.create(title="one", project=project)
        lg2 = LeadGroupFactory.create(title="two", project=project)
        lg3 = LeadGroupFactory.create(title="twoo", project=project)
        obtained = self.filter_class(data=dict(search="tw")).qs
        expected = [lg2, lg3]
        self.assertQuerySetIdEqual(expected, obtained)
