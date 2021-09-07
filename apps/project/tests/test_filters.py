from utils.graphene.tests import GraphQLTestCase

from project.factories import ProjectFactory
from organization.factories import OrganizationFactory
from analysis_framework.factories import AnalysisFrameworkFactory

from project.filter_set import ProjectGqlFilterSet
from project.models import Project


class TestProjectFilter(GraphQLTestCase):
    def setUp(self) -> None:
        self.filter_class = ProjectGqlFilterSet

    def test_organization_filter(self):
        org1, org2, org3 = OrganizationFactory.create_batch(3)
        p1, p2, p3 = ProjectFactory.create_batch(3)
        p1.organizations.set([org2, org1])
        p2.organizations.set([org2, org3])
        p3.organizations.add(org1)

        obtained = self.filter_class(data=dict(
            organizations=[org3.pk, org2.pk]
        )).qs
        expected = [p2, p1]
        self.assertQuerySetIdEqual(
            expected,
            obtained
        )

    def test_search_filter(self):
        ProjectFactory.create(title='one')
        p2 = ProjectFactory.create(title='two')
        p3 = ProjectFactory.create(title='twoo')
        obtained = self.filter_class(data=dict(
            search='tw'
        )).qs
        expected = [p2, p3]
        self.assertQuerySetIdEqual(
            expected,
            obtained
        )

    def test_status_filter(self):
        p1, p2 = ProjectFactory.create_batch(2, status=Project.Status.ACTIVE)
        p3 = ProjectFactory.create(status=Project.Status.INACTIVE)
        obtained = self.filter_class(data=dict(status=Project.Status.ACTIVE.value)).qs
        expected = [p1, p2]
        self.assertQuerySetIdEqual(
            expected,
            obtained
        )
        obtained = self.filter_class(data=dict(status=Project.Status.INACTIVE.value)).qs
        expected = [p3]
        self.assertQuerySetIdEqual(
            expected,
            obtained
        )

    def test_analysis_framework_filter(self):
        af1, af2, af3 = AnalysisFrameworkFactory.create_batch(3)
        p1 = ProjectFactory.create(analysis_framework=af1)
        p2 = ProjectFactory.create(analysis_framework=af2)
        ProjectFactory.create(analysis_framework=af3)

        obtained = self.filter_class(data=dict(
            analysis_frameworks=[af1.id, af2.id]
        )).qs
        expected = [p2, p1]
        self.assertQuerySetIdEqual(
            expected,
            obtained
        )
