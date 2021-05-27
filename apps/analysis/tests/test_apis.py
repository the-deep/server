from dateutil.relativedelta import relativedelta
from django.utils import timezone

from django.conf import settings
from rest_framework.exceptions import ErrorDetail

from deep.tests import TestCase

from entry.models import Entry
from analysis.models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry,
    DiscardedEntry
)
from organization.models import (
    Organization,
    OrganizationType
)


class TestAnalysisAPIs(TestCase):

    def test_create_analysis_without_pillar(self):
        analysis_count = Analysis.objects.count()
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        url = f'/api/v1/projects/{project.id}/analysis/'
        data = {
            'title': 'Test Analysis',
            'team_lead': user.id,
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(Analysis.objects.count(), analysis_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['teamLead'], user.id)

    def test_create_analysis_with_user_not_project_member(self):
        analysis_count = Analysis.objects.count()
        user = self.create_user()
        user2 = self.create_user()
        project = self.create_project()
        project.add_member(user)
        url = f'/api/v1/projects/{project.id}/analysis/'
        data = {
            'title': 'Test Analysis',
            'team_lead': user.id,
        }
        self.authenticate(user2)
        response = self.client.post(url, data)
        self.assert_403(response)

    def test_create_pillar_from_analysis_api(self):
        analysis_count = Analysis.objects.count()
        pillar_count = AnalysisPillar.objects.count()
        user = self.create_user()
        user2 = self.create_user()
        project = self.create_project()
        project.add_member(user)
        url = f'/api/v1/projects/{project.id}/analysis/'
        data = {
            'title': 'Test Analysis',
            'team_lead': user.id,
            'analysis_pillar': [{
                'main_statement': 'Some main statement',
                'information_gap': 'Some information gap',
                'assignee': user.id,
                'title': 'Some title'
            }]
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(Analysis.objects.count(), analysis_count + 1)
        self.assertEqual(AnalysisPillar.objects.count(), pillar_count + 1)

    def test_create_pillar_from_analysis(self):
        pillar_count = AnalysisPillar.objects.count()
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        analysis = self.create(Analysis, title='Test Analysis', created_by=user)
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/'
        data = {
            'main_statement': 'Some main statement',
            'information_gap': 'Some information gap',
            'assignee': user.id,
            'title': 'Some title'
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(response.data['created_by'], user.id)
        self.assertEqual(AnalysisPillar.objects.count(), pillar_count + 1)

    def test_create_pillar_along_with_statement(self):
        pillar_count = AnalysisPillar.objects.count()
        statement_count = AnalyticalStatement.objects.count()
        entry_count = AnalyticalStatementEntry.objects.count()
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        entry1 = self.create(Entry)
        entry2 = self.create(Entry)
        analysis = self.create(Analysis, title='Test Analysis')
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/'
        data = {
            'main_statement': 'Some main statement',
            'information_gap': 'Some information gap',
            'assignee': user.id,
            'title': 'Some title',
            'analytical_statements': [
                {
                    "statement": "coffee",
                    "order": 1,
                    "client_id": "1",
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": "1",
                            "entry": entry1.id,
                        },
                        {
                            "order": 2,
                            "client_id": "2",
                            "entry": entry2.id
                        }
                    ],
                },
                {
                    "statement": "test",
                    "order": 2,
                    "client_id": "2",
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": "1",
                            "entry": entry1.id,
                        }
                    ],
                }
            ]
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(AnalysisPillar.objects.count(), pillar_count + 1)
        self.assertEqual(AnalyticalStatement.objects.filter(
                         analysis_pillar__analysis=analysis).count(), statement_count + 2)

        # try to edit
        response_id = response.data['id']
        data = {
            'main_statement': 'HELLO FROM MARS',
            'analytical_statements': [
                {
                    'statement': "tea",
                    'order': 1,
                    "client_id": "1",
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": "1",
                            "entry": entry1.id,
                        },
                        {
                            "order": 2,
                            "client_id": "2",
                            "entry": entry2.id
                        }
                    ],
                },
            ]
        }
        self.authenticate(user)
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/{response_id}/'
        response = self.client.patch(url, data)
        self.assert_200(response)
        self.assertEqual(response.data['main_statement'], data['main_statement'])
        self.assertEqual(response.data['analytical_statements'][0]['statement'],
                         data['analytical_statements'][0]['statement'])
        # not passing all the resources the data must be deleted from the database
        self.assertEqual(AnalyticalStatement.objects.filter(
                         analysis_pillar__analysis=analysis).count(), statement_count + 1)
        self.assertIn(response.data['analytical_statements'][0]['id'],
                      list(AnalyticalStatement.objects.filter(
                           analysis_pillar__analysis=analysis).values_list('id', flat=True)),)
        # checking for the entries
        self.assertEqual(AnalyticalStatementEntry.objects.filter(
                         analytical_statement__analysis_pillar__analysis=analysis).count(), entry_count + 2)

    def test_create_analytical_statement(self):
        statement_count = AnalyticalStatement.objects.count()
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        entry = self.create(Entry)
        analysis = self.create(Analysis, title='Test Analysis', project=project)
        pillar = self.create(AnalysisPillar, analysis=analysis)
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/{pillar.id}/analytical-statement/'
        data = {
            "analytical_entries": [
                {
                    "order": 1,
                    "client_id": "1",
                    "entry": entry.id
                }
            ],
            "statement": "test statement",
            "order": 1,
            "client_id": "1",
            "analysisPillar": pillar.id
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(AnalyticalStatement.objects.filter(
                         analysis_pillar__analysis=analysis).count(), statement_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['statement'], data['statement'])

    def test_create_analytical_statement_greater_than_30_api_level(self):
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        entry = self.create(Entry)
        analysis = self.create(Analysis, project=project)

        data = {
            'main_statement': 'Some main statement',
            'information_gap': 'Some information gap',
            'assignee': user.id,
            'title': 'Some title',
            'analytical_statements': [
                {
                    "statement": "coffee",
                    "order": 1,
                    "client_id": "1",
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": "1",
                            "entry": entry.id,
                        }
                    ]
                } for _ in range(settings.ANALYTICAL_STATEMENT_COUNT)
            ]
        }
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/'
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)

        # posting statement greater than `ANALYTICAL_STATEMENT_COUNT`
        data = {
            'main_statement': 'Some main statement',
            'information_gap': 'Some information gap',
            'assignee': user.id,
            'title': 'Some title',
            'analytical_statements': [
                {
                    "statement": "coffee",
                    "order": 1,
                    "client_id": "1",
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": "1",
                            "entry": entry.id,
                        }
                    ]
                } for _ in range(settings.ANALYTICAL_STATEMENT_COUNT + 1)
            ]
        }
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/'
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_400(response)
        self.assertIn('non_field_errors', response.data['errors'])

    def test_create_analytical_entries_greater_than_50_api_level(self):
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        entries_list = [self.create(Entry) for _ in range(settings.ANALYTICAL_ENTRIES_COUNT)]
        entries_list_one_more = [self.create(Entry) for _ in range(settings.ANALYTICAL_ENTRIES_COUNT + 1)]
        analysis = self.create(Analysis, project=project)

        data = {
            'main_statement': 'Some main statement',
            'information_gap': 'Some information gap',
            'assignee': user.id,
            'title': 'Some title',
            'analytical_statements': [
                {
                    "statement": "coffee",
                    "order": 1,
                    "client_id": "1",
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": str(entry.id),
                            "entry": entry.id,
                        } for entry in entries_list
                    ]
                }
            ]
        }
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/'
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)

        # try posting for entries less than `ANALYTICAL_ENTRIES_COUNT + 1`
        data = {
            'main_statement': 'Some main statement',
            'information_gap': 'Some information gap',
            'assignee': user.id,
            'title': 'Some title',
            'analytical_statements': [
                {
                    "statement": "coffee",
                    "order": 1,
                    "client_id": "1",
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": str(entry.id),
                            "entry": entry.id,
                        } for entry in entries_list_one_more
                    ]
                }
            ]
        }
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/'
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_400(response)

    def test_version_change_upon_changes_in_analytical_statement(self):
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        self.create_entry(project=project)
        self.create_entry(project=project)
        analysis = self.create(Analysis, title='Test Analysis')
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/'
        data = {
            'main_statement': 'Some main statement',
            'information_gap': 'Some information gap',
            'assignee': user.id,
            'title': 'Some title',
            'analytical_statements': [
                {
                    "statement": "coffee",
                    "order": 1,
                    "client_id": "1"
                },
            ]
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)
        id = response.data['id']
        statement_id = response.data['analytical_statements'][0]['id']
        self.assertEqual(response.data['version_id'], 1)
        # try to patch some changes in analytical_statements
        data = {
            'main_statement': 'Some main statement',
            'information_gap': 'Some not information gap',
            'assignee': user.id,
            'title': 'Some title',
            'analytical_statements': [
                {
                    'id': statement_id,
                    "statement": "tea",
                    "order": 1,
                    "client_id": "123"
                },
            ]
        }
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/{id}/'
        response = self.client.patch(url, data)
        self.assert_200(response)
        # after the sucessfull patch the version should change
        self.assertEqual(response.data['version_id'], 2)

    def test_nested_entry_validation(self):
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        entry1 = self.create(Entry)
        entry2 = self.create(Entry)
        analysis = self.create(Analysis, title='Test Analysis')
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/'
        data = {
            'main_statement': 'Some main statement',
            'information_gap': 'Some information gap',
            'assignee': user.id,
            'title': 'Some title',
            'analytical_statements': [
                {
                    "statement": "coffee",
                    "order": 1,
                    "client_id": "1",
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": "1",
                            "entry": entry1.id,
                        },
                        {
                            "order": 2,
                            "client_id": "2",
                            "entry": entry2.id
                        }
                    ],
                },
                {
                    "statement": "test",
                    "order": 2,
                    "client_id": "2",
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": "1",
                            "entry": entry1.id,
                        }
                    ],
                }
            ]
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)
        response_id = response.data['id']

        # now ty to delete an entry
        Entry.objects.filter(id=entry2.id).delete()
        # try to patch
        data = {
            'main_statement': 'Some main change',
            'information_gap': 'Some information gap',
            'assignee': user.id,
            'title': 'Some title',
            'analytical_statements': [
                {
                    "statement": "coffee",
                    "order": 1,
                    "client_id": "1",
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": "1",
                            "entry": entry1.id,
                        },
                        {
                            "order": 2,
                            "client_id": "2",
                            "entry": entry2.id
                        }
                    ],
                },
                {
                    "statement": "test",
                    "order": 2,
                    "client_id": "2",
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": "1",
                            "entry": entry1.id,
                        }
                    ],
                }
            ]
        }
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/{response_id}/'
        response = self.client.patch(url, data)
        self.assert_400(response)
        self.assertEqual(
            response.data['errors']['analytical_statements'][0]['analytical_entries'][1]['entry'][0],
            ErrorDetail(string=f'Invalid pk "{entry2.id}" - object does not exist.', code='does_not_exist'),
        )
        # TODO: Make sure the error is structured for client
        # self.assertEqual(
        #     response.json()['errors']['analyticalStatements'][0]['analyticalEntries'][1]['entry'][0],
        #     {'string': f'Invalid pk "{entry2.id}" - object does not exist.', 'code': 'does_not_exist'},
        # )

    def test_summary_for_analysis(self):
        user = self.create_user()
        user2 = self.create_user()
        project = self.create_project()
        project.add_member(user)

        now = timezone.now()
        lead1 = self.create_lead(project=project, created_at=now + relativedelta(days=-1))
        lead2 = self.create_lead(project=project, created_at=now)
        self.create_lead(project=project, created_at=now + relativedelta(days=-3))
        entry = self.create_entry(lead=lead1, project=project)
        entry1 = self.create_entry(lead=lead2, project=project)
        entry2 = self.create_entry(lead=lead1, project=project)
        self.create_entry(lead=lead2, project=project)

        analysis1 = self.create(Analysis, title='Test Analysis', team_lead=user, project=project)
        analysis2 = self.create(Analysis, title='Not for test', team_lead=user, project=project)
        pillar1 = self.create(AnalysisPillar, analysis=analysis1, title='title1', assignee=user)
        pillar2 = self.create(AnalysisPillar, analysis=analysis1, title='title2', assignee=user)
        pillar3 = self.create(AnalysisPillar, analysis=analysis1, title='title3', assignee=user2)
        pillar4 = self.create(AnalysisPillar, analysis=analysis2, title='title3', assignee=user2)

        analytical_statement1 = self.create(AnalyticalStatement, analysis_pillar=pillar1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement1, entry=entry)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement1, entry=entry1)

        analytical_statement2 = self.create(AnalyticalStatement, analysis_pillar=pillar2)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement2, entry=entry)

        analytical_statement3 = self.create(AnalyticalStatement, analysis_pillar=pillar3)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement3, entry=entry)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement3, entry=entry1)

        analytical_statement4 = self.create(AnalyticalStatement, analysis_pillar=pillar4)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement4, entry=entry)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement4, entry=entry1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement4, entry=entry2)

        url = f'/api/v1/projects/{project.id}/analysis/summary/'
        self.authenticate(user)
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data
        self.assertEqual(data[1]['team_lead'], user.id)
        self.assertEqual(data[1]['team_lead_name'], user.username)
        self.assertEqual(len(data[1]['pillar_list']), 3)
        self.assertEqual(data[1]['pillar_list'][0]['id'], pillar3.id)
        self.assertEqual(data[1]['pillar_list'][1]['title'], pillar2.title)
        self.assertEqual(data[1]['pillar_list'][2]['assignee_username'], pillar1.assignee.username)
        self.assertEqual(data[1]['analytical_statement_count'], 3)
        self.assertEqual(data[1]['entries_used_in_analysis'], 3)
        self.assertEqual(data[1]['analysis_overview']['entries_analyzed'], 2)
        self.assertEqual(data[1]['analysis_overview']['sources_analyzed'], 2)
        self.assertEqual(data[1]['total_sources'], 2)
        self.assertEqual(data[1]['total_entries'], 4)
        self.assertEqual(data[1]['publication_date']['start_date'], lead1.created_at.date())  # since we use lead that has entry created for
        self.assertEqual(data[1]['publication_date']['end_date'], lead2.created_at.date())
        self.assertEqual(data[1]['framework_overview'][0]['title'], pillar3.title)
        self.assertEqual(data[1]['framework_overview'][0]['entries_count'], 2)
        self.assertEqual(data[1]['framework_overview'][1]['entries_count'], 1)
        self.assertEqual(data[0]['team_lead'], user.id)
        self.assertEqual(data[0]['team_lead_name'], user.username)
        self.assertEqual(data[0]['analysis_overview']['entries_analyzed'], 3)
        self.assertEqual(data[0]['analysis_overview']['sources_analyzed'], 2)

        # try to post to api
        data = {
            'team_lead': user.id,
            'team_lead_name': user.username
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_405(response)

        # try get summary by user that is not member of project
        self.authenticate(user2)
        response = self.client.get(url)
        self.assert_403(response)

    def test_clone_analysis(self):
        user = self.create_user()
        user2 = self.create_user()
        project = self.create_project()
        project.add_member(user)
        analysis = self.create(Analysis, project=project, title="Test Clone")

        url = url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/clone-analysis/'
        data = {
            'title': 'cloned_title',
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertNotEqual(response.data['id'], analysis.id)
        self.assertEqual(response.data['title'], f'{analysis.title} (cloned)')

        # authenticating with user that is not project member
        self.authenticate(user2)
        response = self.client.post(url, data)
        self.assert_403(response)

    def test_patch_analytical_statement(self):
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        entry1 = self.create(Entry)
        entry2 = self.create(Entry)
        analysis = self.create(Analysis)
        pillar = self.create(AnalysisPillar, analysis=analysis, title='title1', assignee=user)
        analytical_statement = self.create(
            AnalyticalStatement,
            analysis_pillar=pillar,
            statement='Hello from here',
            client_id='1'
        )
        staatement_entry1 = self.create(
            AnalyticalStatementEntry,
            analytical_statement=analytical_statement,
            entry=entry1,
            order=1,
            client_id='1'
        )
        statement_entry2 = self.create(
            AnalyticalStatementEntry,
            analytical_statement=analytical_statement,
            entry=entry2,
            order=2,
            client_id='2'
        )
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/{pillar.id}/'
        data = {
            'analytical_statements': [
                {
                    'id': analytical_statement.id,
                    "client_id": str(analytical_statement.id),
                    'statement': 'Hello from there',
                    "analytical_entries": [
                        {
                            "order": 1,
                            "client_id": "1",
                            "entry": entry2.id,
                        },
                        {
                            "order": 2,
                            "client_id": "2",
                            "entry": entry1.id
                        }
                    ],
                }
            ]
        }
        self.authenticate(user)
        response = self.client.patch(url, data)
        self.assert_200(response)
        self.assertEqual(response.data['analytical_statements'][0]['id'], analytical_statement.id)
        self.assertEqual(response.data['analytical_statements'][0]['analytical_entries'][0]['entry'],
                         statement_entry2.entry.id)

    def test_pillar_overview_in_analysis(self):
        user = self.create_user()
        user2 = self.create_user()
        entry = self.create_entry()
        entry1 = self.create_entry()
        entry2 = self.create_entry()
        project = self.create_project()
        project.add_member(user)
        analysis1 = self.create(Analysis, title='Test Analysis', team_lead=user, project=project)
        pillar1 = self.create(AnalysisPillar, analysis=analysis1, title='title1', assignee=user)
        pillar2 = self.create(AnalysisPillar, analysis=analysis1, title='title2', assignee=user)

        analytical_statement1 = self.create(AnalyticalStatement, analysis_pillar=pillar1)
        analytical_statement2 = self.create(AnalyticalStatement, analysis_pillar=pillar1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement1, entry=entry)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement1, entry=entry1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement2, entry=entry2)

        analytical_statement3 = self.create(AnalyticalStatement, analysis_pillar=pillar2)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement3)

        url = f'/api/v1/projects/{project.id}/analysis/{analysis1.id}/pillar-overview/'
        self.authenticate(user)
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data
        self.assertEqual(data[0]['pillar_title'], pillar2.title)
        self.assertEqual(len(data[0]['analytical_statements']), 1)
        self.assertEqual(data[0]['analytical_statements'][0]['entries_count'], 1)
        self.assertEqual(data[0]['analytical_statement_count'], 1)
        self.assertEqual(data[1]['analytical_statement_count'], 2)

        # try to post to api
        data = {
            'assignee': user.id
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_405(response)

        # try get pillar-overview by user that is not member of project
        self.authenticate(user2)
        response = self.client.get(url)
        self.assert_403(response)

    def test_analysis_overview_in_project(self):
        user = self.create_user()
        user2 = self.create_user()
        project = self.create_project()
        project.add_member(user)

        organization_type1 = self.create(OrganizationType, title='OrgA')
        organization_type2 = self.create(OrganizationType, title='Orgb')

        organization1 = self.create(Organization, title='UN', organization_type=organization_type1)
        organization2 = self.create(Organization, title='RED CROSS', organization_type=organization_type2)
        organization3 = self.create(Organization, title='ToggleCorp', organization_type=organization_type1)

        lead1 = self.create_lead(authors=[organization1], project=project, title='TESTA')
        lead2 = self.create_lead(authors=[organization2, organization3], project=project, title='TESTB')
        lead3 = self.create_lead(authors=[organization3], project=project, title='TESTC')
        self.create_lead(authors=[organization2], project=project, title='TESTD')

        entry1 = self.create_entry(lead=lead1, project=project)
        entry2 = self.create_entry(lead=lead2, project=project)
        entry3 = self.create_entry(lead=lead3, project=project)
        self.create_entry(lead=lead3, project=project)

        analysis1 = self.create(Analysis, title='Test Analysis', team_lead=user, project=project)
        analysis2 = self.create(Analysis, title='Test Analysis New', team_lead=user, project=project)
        pillar1 = self.create(AnalysisPillar, analysis=analysis1, title='title1')
        pillar2 = self.create(AnalysisPillar, analysis=analysis2, title='title2')

        analytical_statement1 = self.create(AnalyticalStatement, analysis_pillar=pillar1)
        analytical_statement2 = self.create(AnalyticalStatement, analysis_pillar=pillar1)
        analytical_statement3 = self.create(AnalyticalStatement, analysis_pillar=pillar1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement1, entry=entry1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement2, entry=entry1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement3, entry=entry2)

        analytical_statement3 = self.create(AnalyticalStatement, analysis_pillar=pillar2)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement3, entry=entry3)

        url = f'/api/v1/projects/{project.id}/analysis-overview/'
        self.authenticate(user)
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data

        self.assertEqual(len(data['analysis_list']), 2)
        self.assertEqual(data['analysis_list'][1]['title'], analysis1.title)
        self.assertEqual(data['entries_total'], 4)
        self.assertEqual(data['sources_total'], 3)  # since we take only that lead which entry has been created
        self.assertEqual(data['analyzed_source_count'], 3)
        self.assertEqual(data['analyzed_entries_count'], 3)
        self.assertEqual(len(data['authoring_organizations']), 2)
        self.assertIn(organization_type1.id, [item['organization_type_id'] for item in data['authoring_organizations']])
        self.assertIn(
            organization_type1.title,
            [item['organization_type_title'] for item in data['authoring_organizations']]
        )
        self.assertEqual(set([item['count'] for item in data['authoring_organizations']]), set([1, 3]))

        # authenticate with user that is not project member
        self.authenticate(user2)
        response = self.client.get(url)
        self.assert_403(response)

    def test_post_discarded_entries_in_analysis_pillar(self):
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        entry = self.create_entry(project=project)
        analysis = self.create(Analysis, project=project)
        pillar1 = self.create(AnalysisPillar, analysis=analysis)
        data = {
            'entry': entry.id,
            'tag': DiscardedEntry.TagType.REDUNDANT
        }
        url = f'/api/v1/analysis-pillar/{pillar1.id}/discarded-entries/'
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(response.data['analysis_pillar'], pillar1.id)
        self.assertEqual(response.data['entry'], entry.id)
        self.assertIn('entry_details', response.data)
        self.assertEqual(response.data['entry_details']['id'], entry.id)

        # try to authenticate with user that is not project member
        user2 = self.create_user()
        self.authenticate(user2)
        response = self.client.get(url)
        self.assert_403(response)

        entry1 = self.create_entry()
        data = {
            'entry': entry1.id,
            'tag': DiscardedEntry.TagType.REDUNDANT
        }
        url = f'/api/v1/analysis-pillar/{pillar1.id}/discarded-entries/'
        self.authenticate(user2)
        response = self.client.post(url, data)
        self.assert_403(response)

        # try to post entry that has different project than analysis pillar project
        user2 = self.create_user()
        project2 = self.create_project()
        project2.add_member(user2)
        entry = self.create_entry(project=project2)
        data = {
            'entry': entry.id,
            'tag': DiscardedEntry.TagType.REDUNDANT,
        }
        url = f'/api/v1/analysis-pillar/{pillar1.id}/discarded-entries/'
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_400(response)

    def test_discarded_entries_tag_filter(self):
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        analysis = self.create(Analysis, project=project)
        pillar = self.create(AnalysisPillar, analysis=analysis)
        self.create(DiscardedEntry, analysis_pillar=pillar, tag=DiscardedEntry.TagType.REDUNDANT)
        self.create(DiscardedEntry, analysis_pillar=pillar, tag=DiscardedEntry.TagType.TOO_OLD)
        self.create(DiscardedEntry, analysis_pillar=pillar, tag=DiscardedEntry.TagType.TOO_OLD)
        self.create(DiscardedEntry, analysis_pillar=pillar, tag=DiscardedEntry.TagType.OUTLIER)

        url = f'/api/v1/analysis-pillar/{pillar.id}/discarded-entries/?tag={DiscardedEntry.TagType.TOO_OLD.value}'
        self.authenticate(user)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 2)  # Two discarded entries be present

        # filter by member that is not project member
        user2 = self.create_user()
        self.authenticate(user2)
        response = self.client.get(url)
        self.assert_403(response)

    def test_all_entries_in_analysis_pillar(self):
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        analysis = self.create(Analysis, project=project)
        pillar = self.create(AnalysisPillar, analysis=analysis)
        entry1 = self.create(Entry, project=project)
        self.create(Entry, project=project)
        self.create(Entry, project=project)
        self.create(Entry, project=project)

        # Check the entry count
        analysis_pillar_entries_url = f'/api/v1/analysis-pillar/{pillar.id}/entries/'
        self.authenticate(user)
        response = self.client.post(analysis_pillar_entries_url)
        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 4)  # this should list all the entries present

        # now try to discard the entry from the discarded entries api
        data = {
            'entry': entry1.id,
            'tag': DiscardedEntry.TagType.REDUNDANT
        }
        self.authenticate(user)
        response = self.client.post(f'/api/v1/analysis-pillar/{pillar.id}/discarded-entries/', data)
        self.assert_201(response)

        # try checking the entries that are discarded
        self.authenticate(user)
        response = self.post_filter_test(analysis_pillar_entries_url, {'discarded': True}, count=1)
        response_id = [res['id'] for res in response.data['results']]
        self.assertIn(entry1.id, response_id)

        # try checking the entries that are not discarded
        self.authenticate(user)
        response = self.post_filter_test(analysis_pillar_entries_url, {'discarded': False}, count=3)
        response_id = [res['id'] for res in response.data['results']]
        self.assertNotIn(entry1.id, response_id)

    def test_discardedentry_options(self):
        url = '/api/v1/discardedentry-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertIn('discarded_entries_tags', response.data)
        self.assertEqual(
            response.data['discarded_entries_tags'][0]['key'],
            DiscardedEntry.TagType.REDUNDANT)
        self.assertEqual(
            response.data['discarded_entries_tags'][0]['value'],
            DiscardedEntry.TagType.REDUNDANT.name.title()
        )
        self.assertEqual(
            response.data['discarded_entries_tags'][1]['key'],
            DiscardedEntry.TagType.TOO_OLD)
        self.assertEqual(
            response.data['discarded_entries_tags'][1]['value'],
            DiscardedEntry.TagType.TOO_OLD.name.title()
        )
