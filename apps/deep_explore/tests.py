from utils.graphene.tests import GraphQLSnapShotTestCase

from organization.factories import OrganizationFactory
from user.factories import UserFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from project.factories import ProjectFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory


class TestDeepExploreStats(GraphQLSnapShotTestCase):
    def setUpClass(cls):
        user = UserFactory.create()
        user2, _ = UserFactory.create_batch(2)
        organization1, organization2, _ = OrganizationFactory.create_batch(3)
        analysis_framework, analysis_framework2 = AnalysisFrameworkFactory.create_batch(2)

        project_1 = cls.update_obj(ProjectFactory.create(analysis_framework=analysis_framework), created_at="2020-10-11")
        project_2 = cls.update_obj(ProjectFactory.create(analysis_framework=analysis_framework), created_at="2022-10-11")
        project_3 = cls.update_obj(ProjectFactory.create(analysis_framework=analysis_framework2), created_at="2021-10-11")
        project_4 = cls.update_obj(ProjectFactory.create(analysis_framework=analysis_framework), created_at="2024-10-11")
        project_5 = cls.update_obj(ProjectFactory.create(analysis_framework=analysis_framework), created_at="2021-10-11")
        project_6 = cls.update_obj(ProjectFactory.create(analysis_framework=analysis_framework2), created_at="2023-10-11")
        project_7 = cls.update_obj(ProjectFactory.create(analysis_framework=analysis_framework2), created_at="2020-11-11")
        project_8 = cls.update_obj(ProjectFactory.create(analysis_framework=analysis_framework2), created_at="2020-09-11")

        # Some leads
        lead_1 = cls.update_obj(LeadFactory.create(
            project=project_1, source=organization1,
            created_by=user,
        ), created_at="2020-10-11")
        lead_1.authors.add(organization1)
        lead_2 = cls.update_obj(
            LeadFactory.create(project=project_2, source=organization2, created_by=user), created_at="2020-10-11"
        )
        lead_2.authors.add(organization2)
        cls.update_obj(LeadFactory.create(project=project_3), created_at="2021-10-11")
        cls.update_obj(
            LeadFactory.create(project=project_4, source=organization2, created_by=user2), created_at="2024-10-11"
        )
        lead_5 = cls.update_obj(LeadFactory.create(project=project_5), created_at="2021-10-11")
        lead_5.authors.add(organization1)
        cls.update_obj(LeadFactory.create(project=project_6, created_by=user), created_at="2023-10-11")
        lead_7 = cls.update_obj(
            LeadFactory.create(project=project_7, source=organization1, created_by=user2), created_at="2020-11-11"
        )
        lead_7.authors.add(organization2)
        cls.update_obj(
            LeadFactory.create(project=project_8, source=organization1, created_by=user2), created_at="2020-09-11"
        )

        # Some entry
        cls.update_obj(EntryFactory.create(project=project_1, created_by=user, lead=lead_1), created_at="2020-10-11")
        cls.update_obj(EntryFactory.create(project=project_2, lead=lead_1), created_at="2022-10-11")
        cls.update_obj(EntryFactory.create(project=project_3, created_by=user2, lead=lead_2), created_at="2021-10-11")
        cls.update_obj(EntryFactory.create(project=project_4, created_by=user, lead=lead_5), created_at="2024-10-11")
        cls.update_obj(EntryFactory.create(project=project_5, lead=lead_1), created_at="2021-10-11")
        cls.update_obj(EntryFactory.create(project=project_6, lead=lead_2), created_at="2023-10-11")
        cls.update_obj(EntryFactory.create(project=project_7, created_by=user2, lead=lead_5), created_at="2020-11-11")
        cls.update_obj(EntryFactory.create(project=project_8, created_by=user, lead=lead_7), created_at="2020-09-11")

    def test_explore_deep_dashboard(self):
        query = """
            query MyQuery($filter: ExploreDeepFilter!) {
                deepExploreStats(filter: $filter) {
                    topTenAuthors {
                        id
                        sourceCount
                        projectCount
                    }
                    topTenFrameworks {
                        analysisFrameworkId
                        analysisFrameworkTitle
                        entryCount
                        projectCount
                    }
                    topTenProjectEntries {
                        entryCount
                        projectId
                        projectTitle
                        sourceCount
                    }
                    topTenProjectUsers {
                        projectId
                        projectTitle
                        userCount
                    }
                    topTenPublishers {
                        id
                        sourceCount
                        projectCount
                    }
                    totalActiveUsers
                    totalAuthors
                    totalEntries
                    totalLeads
                    totalProjects
                    totalPublishers
                    totalRegisteredUsers
                }
            }
        """

        user = UserFactory.create()
        user2, _ = UserFactory.create_batch(2)
        organization1, organization2, _ = OrganizationFactory.create_batch(3)
        analysis_framework, analysis_framework2 = AnalysisFrameworkFactory.create_batch(2)

        project_1 = self.update_obj(ProjectFactory.create(analysis_framework=analysis_framework), created_at="2020-10-11")
        project_2 = self.update_obj(ProjectFactory.create(analysis_framework=analysis_framework), created_at="2022-10-11")
        project_3 = self.update_obj(ProjectFactory.create(analysis_framework=analysis_framework2), created_at="2021-10-11")
        project_4 = self.update_obj(ProjectFactory.create(analysis_framework=analysis_framework), created_at="2024-10-11")
        project_5 = self.update_obj(ProjectFactory.create(analysis_framework=analysis_framework), created_at="2021-10-11")
        project_6 = self.update_obj(ProjectFactory.create(analysis_framework=analysis_framework2), created_at="2023-10-11")
        project_7 = self.update_obj(ProjectFactory.create(analysis_framework=analysis_framework2), created_at="2020-11-11")
        project_8 = self.update_obj(ProjectFactory.create(analysis_framework=analysis_framework2), created_at="2020-09-11")

        # Some leads
        lead_1 = self.update_obj(LeadFactory.create(
            project=project_1, source=organization1,
            created_by=user,
        ), created_at="2020-10-11")
        lead_1.authors.add(organization1)
        lead_2 = self.update_obj(
            LeadFactory.create(project=project_2, source=organization2, created_by=user), created_at="2020-10-11"
        )
        lead_2.authors.add(organization2)
        self.update_obj(LeadFactory.create(project=project_3), created_at="2021-10-11")
        self.update_obj(
            LeadFactory.create(project=project_4, source=organization2, created_by=user2), created_at="2024-10-11"
        )
        lead_5 = self.update_obj(LeadFactory.create(project=project_5), created_at="2021-10-11")
        lead_5.authors.add(organization1)
        self.update_obj(LeadFactory.create(project=project_6, created_by=user), created_at="2023-10-11")
        lead_7 = self.update_obj(
            LeadFactory.create(project=project_7, source=organization1, created_by=user2), created_at="2020-11-11"
        )
        lead_7.authors.add(organization2)
        self.update_obj(
            LeadFactory.create(project=project_8, source=organization1, created_by=user2), created_at="2020-09-11"
        )

        # Some entry
        self.update_obj(EntryFactory.create(project=project_1, created_by=user, lead=lead_1), created_at="2020-10-11")
        self.update_obj(EntryFactory.create(project=project_2, lead=lead_1), created_at="2022-10-11")
        self.update_obj(EntryFactory.create(project=project_3, created_by=user2, lead=lead_2), created_at="2021-10-11")
        self.update_obj(EntryFactory.create(project=project_4, created_by=user, lead=lead_5), created_at="2024-10-11")
        self.update_obj(EntryFactory.create(project=project_5, lead=lead_1), created_at="2021-10-11")
        self.update_obj(EntryFactory.create(project=project_6, lead=lead_2), created_at="2023-10-11")
        self.update_obj(EntryFactory.create(project=project_7, created_by=user2, lead=lead_5), created_at="2020-11-11")
        self.update_obj(EntryFactory.create(project=project_8, created_by=user, lead=lead_7), created_at="2020-09-11")

        def _query_check(filter=None, **kwargs):
            return self.query_check(
                query,
                variables={
                    'filter': filter,
                },
                **kwargs
            )

        filter = {
            "dateFrom": "2020-10-01",
            "dateTo": "2021-11-11"
        }
        self.force_login(user)
        content = _query_check(filter)['data']['deepExploreStats']
        self.assertIsNotNone(content, content)
        self.assertEqual(content['totalActiveUsers'], 3)
        self.assertEqual(content['totalAuthors'], 3)
        self.assertEqual(content['totalEntries'], 4)
        self.assertEqual(content['totalLeads'], 4)
        self.assertEqual(content['totalProjects'], 4)
        self.assertEqual(content['totalPublishers'], 2)
        self.assertEqual(content['totalRegisteredUsers'], 3)
