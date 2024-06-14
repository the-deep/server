import datetime

from analysis.factories import AnalysisFactory, AnalysisPillarFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from entry.factories import EntryFactory
from lead.factories import LeadFactory
from project.factories import ProjectFactory
from user.factories import UserFactory

from utils.graphene.tests import GraphQLTestCase


class TestAnalysisQuerySchema(GraphQLTestCase):
    def test_analyses_and_analysis_pillars_query(self):
        # Permission checks
        query = """
            query MyQuery ($projectId: ID!) {
              project(id: $projectId) {
                analyses {
                  totalCount
                  results {
                      id
                      title
                  }
                }
                analysisPillars {
                  totalCount
                  results {
                      id
                      title
                    }
                }
              }
            }
        """

        member_user = UserFactory.create()
        non_member_user = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(member_user, role=self.project_role_reader_non_confidential)
        analyses = AnalysisFactory.create_batch(2, project=project, team_lead=member_user, end_date=datetime.datetime.now())
        for analysis in analyses:
            AnalysisPillarFactory.create_batch(5, analysis=analysis, assignee=member_user)

        def _query_check(**kwargs):
            return self.query_check(query, variables={"projectId": project.id}, **kwargs)

        # -- Without login
        _query_check(assert_for_error=True)

        # --- With login
        self.force_login(non_member_user)
        content = _query_check()
        self.assertEqual(content["data"]["project"]["analyses"]["totalCount"], 0, content)
        self.assertEqual(len(content["data"]["project"]["analyses"]["results"]), 0, content)
        self.assertEqual(content["data"]["project"]["analysisPillars"]["totalCount"], 0, content)
        self.assertEqual(len(content["data"]["project"]["analysisPillars"]["results"]), 0, content)

        self.force_login(member_user)
        content = _query_check()
        self.assertEqual(content["data"]["project"]["analyses"]["totalCount"], 2, content)
        self.assertEqual(len(content["data"]["project"]["analyses"]["results"]), 2, content)
        self.assertEqual(content["data"]["project"]["analysisPillars"]["totalCount"], 10, content)
        self.assertEqual(len(content["data"]["project"]["analysisPillars"]["results"]), 10, content)

    def test_analysis_and_analysis_pillar_query(self):
        # Permission checks
        query = """
            query MyQuery ($projectId: ID!, $analysisId: ID!, $analysisPillarId: ID!) {
              project(id: $projectId) {
                analysis (id: $analysisId) {
                  id
                  title
                }
                analysisPillar (id: $analysisPillarId) {
                  id
                  title
                }
              }
            }
        """

        member_user = UserFactory.create()
        non_member_user = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(member_user, role=self.project_role_reader_non_confidential)
        analysis = AnalysisFactory.create(project=project, team_lead=member_user, end_date=datetime.datetime.now())
        analysis_pillar = AnalysisPillarFactory.create(analysis=analysis, assignee=member_user)

        def _query_check(**kwargs):
            return self.query_check(
                query,
                variables={
                    "projectId": project.id,
                    "analysisId": analysis.id,
                    "analysisPillarId": analysis_pillar.id,
                },
                **kwargs,
            )

        # -- Without login
        _query_check(assert_for_error=True)

        # --- With login
        self.force_login(non_member_user)
        content = _query_check()
        self.assertEqual(content["data"]["project"]["analysis"], None, content)
        self.assertEqual(content["data"]["project"]["analysisPillar"], None, content)

        self.force_login(member_user)
        content = _query_check()
        self.assertNotEqual(content["data"]["project"]["analysis"], None, content)
        self.assertNotEqual(content["data"]["project"]["analysisPillar"], None, content)

    def test_analysis_pillars_entries_query(self):
        query = """
            query MyQuery ($projectId: ID!, $analysisPillarId: ID!) {
              project(id: $projectId) {
                analysisPillar (id: $analysisPillarId) {
                  id
                  title
                  entries {
                    totalCount
                    results {
                      id
                    }
                  }
                }
              }
            }
        """

        now = datetime.datetime.now()
        member_user = UserFactory.create()
        non_member_user = UserFactory.create()
        af = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=af)
        another_project = ProjectFactory.create(analysis_framework=af)
        project.add_member(member_user, role=self.project_role_reader_non_confidential)
        analysis = AnalysisFactory.create(project=project, team_lead=member_user, end_date=now)
        analysis_pillar = AnalysisPillarFactory.create(analysis=analysis, assignee=member_user)

        def _query_check(**kwargs):
            return self.query_check(
                query,
                variables={"projectId": project.id, "analysisPillarId": analysis_pillar.pk},
                **kwargs,
            )

        # -- Without login
        _query_check(assert_for_error=True)

        # --- With login
        self.force_login(non_member_user)
        content = _query_check()
        self.assertEqual(content["data"]["project"]["analysisPillar"], None, content)

        self.force_login(member_user)
        content = _query_check()
        self.assertEqual(content["data"]["project"]["analysisPillar"]["entries"]["totalCount"], 0, content)
        self.assertEqual(len(content["data"]["project"]["analysisPillar"]["entries"]["results"]), 0, content)

        # Let's add some entries
        lead_published_on = now - datetime.timedelta(days=1)  # To fit within analysis end_date
        EntryFactory.create_batch(10, lead=LeadFactory.create(project=project, published_on=lead_published_on))
        EntryFactory.create_batch(8, lead=LeadFactory.create(project=another_project, published_on=lead_published_on))

        content = _query_check()
        self.assertEqual(content["data"]["project"]["analysisPillar"]["entries"]["totalCount"], 10, content)
        self.assertEqual(len(content["data"]["project"]["analysisPillar"]["entries"]["results"]), 10, content)
