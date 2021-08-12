from utils.graphene.tests import GraphQLTestCase

from project.factories import ProjectFactory
from organization.factories import OrganizationFactory
from analysis_framework.factories import AnalysisFrameworkFactory

from project.filter_set import ProjectGqlFilterSet
from project.models import Project

ACTIVE = Project.Status.ACTIVE
INACTIVE = Project.Status.INACTIVE


class TestProjectFilter(GraphQLTestCase):
    def setUp(self) -> None:
        self.filter_class = ProjectGqlFilterSet

    def test_organization_filter(self):
        org1 = OrganizationFactory.create()
        org2 = OrganizationFactory.create()
        org3 = OrganizationFactory.create()
        p1 = ProjectFactory.create()
        p1.organizations.set([org2, org1])
        p2 = ProjectFactory.create()
        p2.organizations.set([org2, org3])
        p3 = ProjectFactory.create()
        p3.organizations.add(org1)

        obtained = self.filter_class(data=dict(
            organizations=[str(org3.id), str(org2.id)]
        )).qs
        expected = [p2, p1]
        self.assertQuerySetEqual(
            expected,
            obtained
        )

    def test_search_filter(self):
        ProjectFactory.create(title='one')
        p2 = ProjectFactory.create(title='two')
        p3 = ProjectFactory.create(title='towo')
        obtained = self.filter_class(data=dict(
            search='w'
        )).qs
        expected = [p2, p3]
        self.assertQuerySetEqual(
            expected,
            obtained
        )

    def test_status_filter(self):
        p1 = ProjectFactory.create(status=ACTIVE)
        p2 = ProjectFactory.create(status=INACTIVE)
        obtained = self.filter_class(data=dict(
            status=[
                ACTIVE.value
            ]
        )).qs
        expected = [p1]
        self.assertQuerySetEqual(
            expected,
            obtained
        )
        obtained = self.filter_class(data=dict(
            status=[
                ACTIVE.value,
                INACTIVE.value,
            ]
        )).qs
        expected = [p1, p2]
        self.assertQuerySetEqual(
            expected,
            obtained
        )

    def test_analysis_framework_filter(self):
        af1 = AnalysisFrameworkFactory.create()
        af2 = AnalysisFrameworkFactory.create()
        af3 = AnalysisFrameworkFactory.create()
        p1 = ProjectFactory.create(analysis_framework=af1)
        p2 = ProjectFactory.create(analysis_framework=af2)
        ProjectFactory.create(analysis_framework=af3)

        obtained = self.filter_class(data=dict(
            analysis_frameworks=[str(af1.id), str(af2.id)]
        )).qs
        expected = [p2, p1]
        self.assertQuerySetEqual(
            expected,
            obtained
        )
