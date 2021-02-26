from deep.tests import TestCase

from project.models import Project
from entry.models import Entry
from user.models import User
from analysis.models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry,
)


class TestAnalysisAPIs(TestCase):

    def test_create_analysis_without_pillar(self):
        analysis_count = Analysis.objects.count()
        user = self.create_user()
        project = self.create_project()
        url = '/api/v1/analysis/'
        data = {
            'title': 'Test Analysis',
            'team_lead': user.id,
            'project': project.id,
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(Analysis.objects.count(), analysis_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['teamLead'], user.id)

    def test_create_pillar_from_analysis(self):
        pillar_count = AnalysisPillar.objects.count()
        user = self.create_user()
        analysis = self.create(Analysis, title='Test Analysis')
        url = f'/api/v1/analysis/{analysis.id}/pillars/'
        data = {
            'main_statement': 'Some main statement',
            'information_gap': 'Some information gap',
            'assignee': user.id,
            'title': 'Some title'
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(AnalysisPillar.objects.count(), pillar_count + 1)

    def test_create_analytical_statement(self):
        statement_count = AnalyticalStatement.objects.count()
        entry = self.create(Entry)
        analysis = self.create(Analysis, title='Test Analysis')
        pillar = self.create(AnalysisPillar, analysis=analysis)
        url = f'/api/v1/analysis/{analysis.id}/pillars/{pillar.id}/analytical-statement/'
        data = {
            "analytical_entries": [
                {
                    "order": 1,
                    "entry": entry.id
                }
            ],
            "statement": "test statement",
            "order": 1,
            "analysisPillar": pillar.id
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(AnalyticalStatement.objects.filter(analysis_pillar__analysis=analysis).count(), statement_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['statement'], data['statement'])

    def test_summary_for_analysis(self):
        user = self.create_user()
        user2 = self.create_user()
        entry = self.create_entry()
        entry1 = self.create_entry()
        analysis1 = self.create(Analysis, title='Test Analysis', team_lead=user)
        analysis2 = self.create(Analysis, title='Not for test', team_lead=user)
        pillar1 = self.create(AnalysisPillar, analysis=analysis1, title='title1', assignee=user)
        pillar2 = self.create(AnalysisPillar, analysis=analysis1, title='title2', assignee=user)
        pillar3 = self.create(AnalysisPillar, analysis=analysis1, title='title3', assignee=user2)

        analytical_statement1 = self.create(AnalyticalStatement, analysis_pillar=pillar1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement1, entry=entry)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement1, entry=entry1)

        analytical_statement2 = self.create(AnalyticalStatement, analysis_pillar=pillar2)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement2, entry=entry)

        analytical_statement3 = self.create(AnalyticalStatement, analysis_pillar=pillar3)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement3, entry=entry)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement3, entry=entry1)

        url = f'/api/v1/analysis/{analysis1.id}/summary/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data
        self.assertEqual(data['team_lead'], user.id)
        self.assertEqual(data['team_lead_name'], user.username)
        self.assertEqual(len(data['pillar_list']), 3)
        self.assertEqual(data['pillar_list'][0]['id'], pillar3.id)
        self.assertEqual(data['pillar_list'][1]['title'], pillar2.title)
        self.assertEqual(data['pillar_list'][2]['assignee'], pillar1.assignee.username)
        self.assertEqual(data['analytical_statement_count'], 3)
        self.assertEqual(data['entries_used_in_analysis'], 3)
        self.assertEqual(data['framework_overview'][0]['title'], pillar3.title)
        self.assertEqual(data['framework_overview'][0]['entries_count'], 2)
        self.assertEqual(data['framework_overview'][1]['entries_count'], 1)
