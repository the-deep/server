from deep.tests import TestCase

from user.models import User
from analysis.models import Analysis, AnalysisPillar


class TestAnalysisAPIs(TestCase):

    def test_create_analysis_without_pillar(self):
        analysis_count = Analysis.objects.count()
        user = self.create_user()

        url = '/api/v1/analysis/'
        data = {
            'title': 'Test Analysis',
            'team_lead': user.id
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Analysis.objects.count(), analysis_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['teamLead'], user.id)

    def test_create_analysis_with_pillar(self):
        analysis_count = Analysis.objects.count()
        pillar_count = AnalysisPillar.objects.count()

        user = self.create_user()

        url = '/api/v1/analysis/'
        data = {
            'analysisPillar': [
                {
                    'main_statement': 'Some main statement',
                    'information_gap': 'Some information gap',
                    'assignee': user.id
                }
            ],
            "title": "dsa",
            "team_lead": user.id
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Analysis.objects.count(), analysis_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])

        # try checking for the pillar as well
        self.assertEqual(AnalysisPillar.objects.filter(analysis=r_data['id']).count(), pillar_count + 1)

    def test_update_pillar_from_analysis(self):
        user = self.create_user()
        user2 = self.create_user()

        url = '/api/v1/analysis/'
        data = {
            'analysis_pillar': [
                {
                    'main_statement': 'Some main statement',
                    'information_gap': 'Some information gap',
                    'assignee': user.id
                }
            ],
            "title": "dsa",
            "team_lead": user.id
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)
        analysis_id = response.data['id']
        pillar_id = response.data['analysis_pillar'][0]['id']

        url1 = f'/api/v1/analysis/{analysis_id}/analysis-pillar/'
        data1 = {
            'id': pillar_id,
            'main_statement': 'main statement',
        }
        self.authenticate()
        response = self.client.patch(url1, data1)
        self.assert_200(response)

    def test_create_analysis_pillar(self):
        """
        Creating pillar from analysis only
        """
        user = self.create_user()
        url = '/api/v1/analysis-pillar/'
        data = {
            'main_statement': 'Some main statement',
            'information_gap': 'Some information gap',
            'assignee': user.id
        }
        self.authenticate()
        response = self.client.post(url, data)
        self.assert_405(response)
