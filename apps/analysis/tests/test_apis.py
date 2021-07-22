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
        now = timezone.now()
        url = f'/api/v1/projects/{project.id}/analysis/'
        data = {
            'title': 'Test Analysis',
            'team_lead': user.id,
            'start_date': (now + relativedelta(days=2)).date(),
            'end_date': (now + relativedelta(days=22)).date(),
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(Analysis.objects.count(), analysis_count + 1)
        r_data = response.json()
        self.assertEqual(r_data['title'], data['title'])
        self.assertEqual(r_data['teamLead'], user.id)

    def test_create_analysis_with_user_not_project_member(self):
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
        self.create_user()
        project = self.create_project()
        project.add_member(user)
        now = timezone.now()
        url = f'/api/v1/projects/{project.id}/analysis/'
        data = {
            'title': 'Test Analysis',
            'team_lead': user.id,
            'start_date': (now + relativedelta(days=2)).date(),
            'end_date': (now + relativedelta(days=22)).date(),
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
        analysis = self.create(Analysis, title='Test Analysis', project=project, created_by=user)
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
        entry1 = self.create_entry(project=project)
        entry2 = self.create_entry(project=project)
        analysis = self.create(Analysis, project=project, title='Test Analysis')
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

    def test_end_date_analysis_greater_than_lead_published_on(self):
        """
        Test for a lead published date after the analysis end_date
        """
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        now = timezone.now()
        lead = self.create_lead(project=project, published_on=now + relativedelta(days=6))
        entry = self.create_entry(project=project, lead=lead)
        analysis = self.create(Analysis, project=project, title='Test Analysis', end_date=now + relativedelta(days=4))
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
                            "entry": entry.id,
                        },
                    ]
                }
            ]
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_400(response)
        self.assertEqual(
            response.data['errors']['analytical_statements'][0]['analytical_entries'][0]['entry'][0],
            ErrorDetail(
                string=f'Entry {entry.id} lead published_on cannot be greater than analysis end_date {analysis.end_date.date()}'
                , code='invalid'
            ),
        )

    def test_analysis_end_date_change(self):
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        now = timezone.now()
        lead = self.create_lead(project=project, published_on=now + relativedelta(days=2))
        entry = self.create_entry(project=project, lead=lead)
        analysis = self.create(Analysis, project=project, title='Test Analysis', end_date=now + relativedelta(days=4))
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
                            "entry": entry.id,
                        },
                    ]
                }
            ]
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)
        # try to change the analysis end_date and try to patch at the pillar
        analysis.end_date = now + relativedelta(days=1)
        analysis.save()
        pillar_id = response.data['id']
        url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/pillars/{pillar_id}/'
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
                        },
                    ]
                }
            ]
        }
        self.authenticate(user)
        response = self.client.patch(url, data)
        self.assert_400(response)

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
        analysis = self.create(Analysis, title='Test Analysis', project=project)
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
        entry1 = self.create_entry(project=project)
        entry2 = self.create_entry(project=project)
        analysis = self.create(Analysis, title='Test Analysis', project=project)
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

        # now try to delete an entry
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
        lead1 = self.create_lead(project=project, published_on=now)
        lead2 = self.create_lead(project=project, published_on=now + relativedelta(days=-1))
        lead3 = self.create_lead(project=project, published_on=now + relativedelta(days=-3))
        lead4 = self.create_lead(project=project, published_on=now + relativedelta(days=5))
        lead5 = self.create_lead(project=project, published_on=now + relativedelta(days=2))
        lead6 = self.create_lead(project=project, published_on=now + relativedelta(days=-3))
        self.create_lead(project=project, published_on=now + relativedelta(days=-2))
        lead8 = self.create_lead(project=project, published_on=now + relativedelta(days=-2))
        lead9 = self.create_lead(project=project, published_on=now + relativedelta(days=-2))
        self.create_lead(project=project, published_on=now + relativedelta(days=-3))
        entry = self.create_entry(lead=lead1, project=project)
        entry1 = self.create_entry(lead=lead2, project=project)
        entry2 = self.create_entry(lead=lead3, project=project)
        entry3 = self.create_entry(lead=lead4, project=project)
        entry4 = self.create_entry(lead=lead5, project=project)
        entry5 = self.create_entry(lead=lead6, project=project)
        entry6 = self.create_entry(lead=lead6, project=project)
        self.create_entry(lead=lead8, project=project)
        entry8 = self.create_entry(lead=lead9, project=project)
        entry9 = self.create_entry(lead=lead2, project=project)

        analysis1 = self.create(
            Analysis,
            title='Test Analysis',
            team_lead=user,
            project=project,
            end_date=now + relativedelta(days=4)
        )
        analysis2 = self.create(
            Analysis,
            title='Not for test',
            team_lead=user,
            project=project,
            end_date=now + relativedelta(days=7)
        )
        pillar1 = self.create(AnalysisPillar, analysis=analysis1, title='title1', assignee=user)
        pillar2 = self.create(AnalysisPillar, analysis=analysis1, title='title2', assignee=user)
        pillar3 = self.create(AnalysisPillar, analysis=analysis1, title='title3', assignee=user2)

        pillar4 = self.create(AnalysisPillar, analysis=analysis2, title='title3', assignee=user2)

        analytical_statement1 = self.create(AnalyticalStatement, analysis_pillar=pillar1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement1, entry=entry)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement1, entry=entry1)
        # lets discard some entry here
        DiscardedEntry.objects.create(
            analysis_pillar=pillar1,
            entry=entry3,
            tag=DiscardedEntry.TagType.REDUNDANT
        )
        DiscardedEntry.objects.create(
            analysis_pillar=pillar1,
            entry=entry9,
            tag=DiscardedEntry.TagType.REDUNDANT
        )

        analytical_statement2 = self.create(AnalyticalStatement, analysis_pillar=pillar2)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement2, entry=entry4)
        DiscardedEntry.objects.create(
            analysis_pillar=pillar2,
            entry=entry5,
            tag=DiscardedEntry.TagType.REDUNDANT
        )

        analytical_statement3 = self.create(AnalyticalStatement, analysis_pillar=pillar3)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement3, entry=entry5)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement3, entry=entry6)
        DiscardedEntry.objects.create(
            analysis_pillar=pillar3,
            entry=entry2,
            tag=DiscardedEntry.TagType.REDUNDANT
        )

        analytical_statement4 = self.create(AnalyticalStatement, analysis_pillar=pillar4)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement4, entry=entry)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement4, entry=entry1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement4, entry=entry2)
        DiscardedEntry.objects.create(
            analysis_pillar=pillar4,
            entry=entry8,
            tag=DiscardedEntry.TagType.REDUNDANT
        )

        url = f'/api/v1/projects/{project.id}/analysis/summary/'
        self.authenticate(user)
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data['results']
        self.assertEqual(data[1]['team_lead'], user.id)
        self.assertEqual(data[1]['end_date'], analysis1.end_date.strftime('%Y-%m-%d'))
        self.assertEqual(data[1]['team_lead_details']['id'], user.id)
        self.assertEqual(data[1]['team_lead_details']['display_name'], user.profile.get_display_name())
        self.assertEqual(data[1]['pillars'][0]['id'], pillar3.id)
        self.assertEqual(data[1]['pillars'][1]['title'], pillar2.title)
        self.assertEqual(
            data[1]['pillars'][2]['assignee_details']['display_name'], pillar1.assignee.profile.get_display_name()
        )
        self.assertEqual(
            data[1]['publication_date']['start_date'], lead6.published_on.strftime('%Y-%m-%d')
        )  # since we use lead that has entry created for
        self.assertEqual(data[1]['publication_date']['end_date'], lead5.published_on.strftime('%Y-%m-%d'))
        self.assertEqual(data[1]['pillars'][0]['analyzed_entries'], 3)  # discrded + analyzed entry
        self.assertEqual(data[1]['pillars'][1]['analyzed_entries'], 2)  # discrded + analyzed entry
        # here considering the entry whose lead published date less than analysis end_date
        self.assertEqual(data[1]['analyzed_entries'], 8)
        self.assertEqual(data[1]['analyzed_sources'], 6)  # have `distinct=True`
        self.assertEqual(data[1]['total_entries'], 10)
        self.assertEqual(data[1]['total_sources'], 8)  # taking lead that has entry more than one
        self.assertEqual(data[0]['team_lead'], user.id)
        self.assertEqual(data[0]['team_lead_details']['id'], user.id)
        self.assertEqual(data[0]['team_lead_details']['display_name'], user.profile.get_display_name())
        self.assertEqual(data[0]['pillars'][0]['id'], pillar4.id)
        self.assertEqual(data[0]['analyzed_entries'], 4)
        self.assertEqual(data[0]['analyzed_sources'], 4)

        # try to post to api
        data = {'team_lead': user.id}
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
        entry = self.create_entry(project=project)
        entry1 = self.create_entry(project=project)
        analysis = self.create(Analysis, project=project, title="Test Clone")
        pillar = self.create(AnalysisPillar, analysis=analysis, title='title1', assignee=user)
        analytical_statement = self.create(
            AnalyticalStatement,
            analysis_pillar=pillar,
            statement='Hello from here',
            client_id='1'
        )
        self.create(
            AnalyticalStatementEntry,
            analytical_statement=analytical_statement,
            entry=entry,
            order=1,
            client_id='1'
        )
        self.create(
            DiscardedEntry,
            entry=entry1,
            analysis_pillar=pillar,
            tag=DiscardedEntry.TagType.REDUNDANT
        )

        url = url = f'/api/v1/projects/{project.id}/analysis/{analysis.id}/clone/'
        # try to post with no end_date
        data = {
            'title': 'cloned_title',
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_400(response)
        assert 'end_date' in response.data
        self.assertEqual(
            response.data['end_date'],
            [ErrorDetail(string='This field is required.', code='required')]
        )

        # try to post with start_date greater than end_date
        data = {
            'title': 'cloned_title',
            'end_date': '2020-10-01',
            'start_date': '2020-10-20'
        }
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_400(response)
        self.assertEqual(
            response.data['end_date'],
            [ErrorDetail(string='End date must occur after start date', code='invalid')]
        )

        data['start_date'] = '2020-09-10'
        self.authenticate(user)
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertNotEqual(response.data['id'], analysis.id)
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['cloned_from'], analysis.id)
        self.assertEqual(response.data['analysis_pillar'][0]['cloned_from'], pillar.id)
        # test if the nested fields are cloned or not
        self.assertEqual(
            Analysis.objects.count(),
            2
        )  # need to be cloned and created by user
        self.assertEqual(
            AnalysisPillar.objects.count(),
            2
        )
        self.assertEqual(
            AnalyticalStatement.objects.count(),
            2
        )
        self.assertEqual(
            AnalyticalStatementEntry.objects.count(),
            2
        )
        self.assertEqual(
            DiscardedEntry.objects.count(),
            2
        )
        # authenticating with user that is not project member
        self.authenticate(user2)
        response = self.client.post(url, data)
        self.assert_403(response)

    def test_patch_analytical_statement(self):
        user = self.create_user()
        project = self.create_project()
        project.add_member(user)
        entry1 = self.create(Entry, project=project)
        entry2 = self.create(Entry, project=project)
        analysis = self.create(Analysis, project=project)
        pillar = self.create(AnalysisPillar, analysis=analysis, title='title1', assignee=user)
        analytical_statement = self.create(
            AnalyticalStatement,
            analysis_pillar=pillar,
            statement='Hello from here',
            client_id='1'
        )
        self.create(
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
        project = self.create_project()
        entry = self.create_entry(project=project)
        entry1 = self.create_entry(project=project)
        entry2 = self.create_entry(project=project)
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

        url = f'/api/v1/projects/{project.id}/analysis/{analysis1.id}/pillars/summary/'
        self.authenticate(user)
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data['results']
        self.assertEqual(data[0]['title'], pillar2.title)
        self.assertEqual(len(data[0]['analytical_statements']), 1)
        self.assertEqual(data[0]['analytical_statements'][0]['entries_count'], 1)
        self.assertEqual(len(data[1]['analytical_statements']), 2)

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
        entry4 = self.create_entry(lead=lead2, project=project)

        analysis1 = self.create(Analysis, title='Test Analysis', team_lead=user, project=project)
        analysis2 = self.create(Analysis, title='Test Analysis New', team_lead=user, project=project)
        pillar1 = self.create(AnalysisPillar, analysis=analysis1, title='title1')
        pillar2 = self.create(AnalysisPillar, analysis=analysis2, title='title2')

        analytical_statement1 = self.create(AnalyticalStatement, analysis_pillar=pillar1)
        analytical_statement2 = self.create(AnalyticalStatement, analysis_pillar=pillar1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement1, entry=entry1)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement2, entry=entry2)
        DiscardedEntry.objects.create(
            analysis_pillar=pillar1,
            entry=entry4,
            tag=DiscardedEntry.TagType.REDUNDANT
        )

        analytical_statement3 = self.create(AnalyticalStatement, analysis_pillar=pillar2)
        self.create(AnalyticalStatementEntry, analytical_statement=analytical_statement3, entry=entry3)

        url = f'/api/v1/projects/{project.id}/analysis-overview/'
        self.authenticate(user)
        response = self.client.get(url)
        self.assert_200(response)
        data = response.data

        self.assertEqual(len(data['analysis_list']), 2)
        self.assertEqual(data['analysis_list'][1]['title'], analysis1.title)
        self.assertEqual(data['entries_total'], 5)
        self.assertEqual(data['sources_total'], 3)  # since we take only that lead which entry has been created
        self.assertEqual(data['analyzed_source_count'], 3)  # since we take entry
        self.assertEqual(data['analyzed_entries_count'], 4)  # discarded + analyzed
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
        now = timezone.now()
        lead = self.create_lead(project=project, published_on=now)
        lead1 = self.create_lead(project=project, published_on=now + relativedelta(days=5))
        entry = self.create_entry(project=project, lead=lead)
        analysis = self.create(Analysis, project=project, end_date=now + relativedelta(days=2))
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

        entry1 = self.create_entry(project=project, lead=lead)
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

        # try to post the entry with lead published date greater than the analysis end_date
        entry2 = self.create_entry(project=project, lead=lead1)
        data = {
            'entry': entry2.id,
            'tag': DiscardedEntry.TagType.REDUNDANT
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
        project2 = self.create_project()
        project2.add_member(user)
        now = timezone.now()
        analysis = self.create(Analysis, project=project, end_date=now)
        pillar = self.create(AnalysisPillar, analysis=analysis)
        lead1 = self.create_lead(project=project, title='TESTA', published_on=now + relativedelta(days=2))
        lead2 = self.create_lead(project=project, title='TESTA', published_on=now + relativedelta(days=-4))
        lead3 = self.create_lead(project=project, title='TESTA', published_on=now + relativedelta(days=-2))
        entry1 = self.create(Entry, project=project, lead=lead2)
        self.create(Entry, project=project, lead=lead2)
        self.create(Entry, project=project, lead=lead3)
        self.create(Entry, project=project, lead=lead1)
        self.create(Entry, project=project2, lead=lead3)

        # Check the entry count
        analysis_pillar_entries_url = f'/api/v1/analysis-pillar/{pillar.id}/entries/'
        self.authenticate(user)
        response = self.client.post(analysis_pillar_entries_url)
        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 3)  # this should list all the entries present

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
        response = self.post_filter_test(analysis_pillar_entries_url, {'discarded': False}, count=2)
        response_id = [res['id'] for res in response.data['results']]
        self.assertNotIn(entry1.id, response_id)

    def test_discardedentry_options(self):
        url = '/api/v1/discarded-entry-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(
            response.data[0]['key'],
            DiscardedEntry.TagType.REDUNDANT)
        self.assertEqual(
            response.data[0]['value'],
            DiscardedEntry.TagType.REDUNDANT.label
        )
        self.assertEqual(
            response.data[1]['key'],
            DiscardedEntry.TagType.TOO_OLD)
        self.assertEqual(
            response.data[1]['value'],
            DiscardedEntry.TagType.TOO_OLD.label
        )
